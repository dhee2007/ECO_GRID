"""Standard-library EcoGrid backend: CPU inference, integrity, fusion, forecasts, incentives."""
import csv,json,math,sqlite3,statistics,time,datetime
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['weight_g','moisture_pct','metal_signal','transparency','acoustic_hardness']
def records(name):
 with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def numeric(v,default=None):
 try:return float(v) if str(v).strip() else default
 except (ValueError,TypeError):return default
class WasteForest:
 def __init__(self,path=None):
  self.data=json.loads(Path(path or ROOT/'models/waste_forest.json').read_text())
  self.classes=self.data['classes'];self.medians=self.data['medians'];self.trees=self.data['trees']
 def predict(self,readings):
  x=[numeric(v,self.medians[f]) for f,v in zip(FEATURES,readings)]
  if len(x)!=5:raise ValueError('Five sensor values are required')
  votes=[0.]*len(self.classes);start=time.perf_counter()
  for tree in self.trees:
   n=0
   while tree['left'][n]!=-1:
    f=tree['feature'][n];n=tree['left'][n] if x[f]<=tree['threshold'][n] else tree['right'][n]
   values=tree['votes'][n];total=sum(values)
   if total:
    for i,v in enumerate(values):votes[i]+=v/total
  probs=[v/len(self.trees) for v in votes];best=max(range(len(probs)),key=lambda i:probs[i]);ms=(time.perf_counter()-start)*1000
  return {'category':self.classes[best],'confidence':round(probs[best]*100,2),'probabilities':dict(zip(self.classes,[round(v*100,2) for v in probs])),'inference_ms':round(ms,3),'imputed_features':[f for f,v in zip(FEATURES,readings) if numeric(v) is None]}
def evaluate(model,rows):
 result=[]
 for i,r in enumerate(rows,1):
  try:
   p=model.predict([r.get(f,'') for f in FEATURES]);actual=(r.get('category') or '').strip();out={'event_id':r.get('event_id') or str(i),'building_id':r.get('building_id',''),'prediction':p['category'],'confidence_pct':p['confidence'],'inference_ms':p['inference_ms'],'actual_category':actual,'correct':('Yes' if p['category']==actual else 'No') if actual else 'Unknown','imputed_features':','.join(p['imputed_features'])};result.append(out)
  except Exception as e:result.append({'event_id':r.get('event_id') or str(i),'error':str(e),'correct':'Invalid'})
 labeled=[r for r in result if r['correct'] in ('Yes','No')]
 return result,{'total':len(result),'labeled':len(labeled),'correct':sum(r['correct']=='Yes' for r in labeled),'accuracy_pct':round(100*sum(r['correct']=='Yes' for r in labeled)/len(labeled),2) if labeled else None}
def fuse_daily():
 """Three sources: daily meters, hourly meters, manual logs. Robust conflict flags, preserve missing buildings."""
 daily=records('daily_summary');hourly=records('hourly_streams');manual=records('manual_logs');buildings=records('buildings')
 names={b['building_name'].lower():b['building_id'] for b in buildings}
 aggregate=defaultdict(lambda:defaultdict(list))
 for r in hourly:
  day=r['timestamp'][:10];key=(day,r['building_id'])
  for col in ('electricity_kwh','water_litres'):
   val=numeric(r.get(col));
   if val is not None and val>=0:aggregate[key][col].append(val)
 manual_agg=defaultdict(lambda:defaultdict(list))
 for r in manual:
  bid=names.get((r.get('building') or '').lower(),r.get('building',''))
  key=(r.get('logged_at','')[:10],bid);stream=(r.get('stream') or '').lower();v=numeric(r.get('value'))
  if v is None:continue
  for col,words in [('electricity_kwh',('electric','energy')),('water_litres',('water','flow'))]:
   if any(w in stream for w in words):manual_agg[key][col].append(v)
 out=[];conflicts=0
 for r in daily:
  key=(r['date'],r['building_id']);row={'date':r['date'],'building_id':r['building_id']}
  for col in ('electricity_kwh','water_litres'):
   daily_val=numeric(r.get(col));hourly_vals=aggregate[key][col];hourly_sum=sum(hourly_vals) if hourly_vals else None
   # Daily total and sum of hourly measurements are comparable. Manual values are audit-only without verified units/interval.
   if daily_val is not None and hourly_sum is not None:
    disagreement=abs(daily_val-hourly_sum)/max(abs(daily_val),1)
    if disagreement>.2:conflicts+=1
    fused=statistics.median([daily_val,hourly_sum]);source='daily+hourly';quality='conflict' if disagreement>.2 else 'normal'
   elif daily_val is not None:fused=daily_val;source='daily';quality='partial'
   elif hourly_sum is not None:fused=hourly_sum;source='hourly';quality='partial'
   else:fused=None;source='unavailable';quality='missing'
   row[col+'_fused']=round(fused,2) if fused is not None else '';row[col+'_quality']=quality;row[col+'_sources']=source;row[col+'_manual_audit_count']=len(manual_agg[key][col])
  out.append(row)
 return out,{'records':len(out),'conflicts':conflicts,'source_types':3,'manual_log_count':len(manual),'note':'Manual entries are used as audit signals because their sampling intervals/units may differ from daily totals.'}
def forecast(building,resource='electricity_kwh',horizon=12):
 rows=sorted((r for r in records('hourly_streams') if r['building_id']==building),key=lambda r:r['timestamp']);split=int(.8*len(rows));train=rows[:split];valid=rows[split:]
 byhour=defaultdict(list)
 for r in train:
  v=numeric(r.get(resource));
  if v is not None:byhour[int(r['timestamp'][11:13])].append(v)
 allvals=[v for values in byhour.values() for v in values]
 if not allvals:raise ValueError('No training readings')
 fallback=statistics.mean(allvals);means={h:statistics.mean(byhour[h]) if byhour[h] else fallback for h in range(24)}
 errs=[abs(numeric(r.get(resource))-means[int(r['timestamp'][11:13])]) for r in valid if numeric(r.get(resource)) is not None]
 last=int(rows[-1]['timestamp'][11:13]);return {'building_id':building,'resource':resource,'next_12_hours':[round(means[(last+h)%24],2) for h in range(1,horizon+1)],'holdout_mae':round(statistics.mean(errs),3) if errs else None,'model':'CPU hour-of-day seasonal mean','tradeoff':'Low memory and fast CPU inference; less responsive to unusual events than larger ML models'}
def offline_db():
 path=ROOT/'data'/'offline_buffer.db';conn=sqlite3.connect(path)
 conn.execute('CREATE TABLE IF NOT EXISTS event_queue(event_id TEXT PRIMARY KEY, building_id TEXT, captured_at TEXT, received_at TEXT, payload TEXT, status TEXT DEFAULT "pending")')
 conn.execute('CREATE TABLE IF NOT EXISTS campus_events(event_id TEXT PRIMARY KEY, building_id TEXT, captured_at TEXT, payload TEXT)');conn.commit();return conn
def enqueue(event_id,building_id,captured_at,payload):
 with offline_db() as c:
  c.execute('INSERT OR IGNORE INTO event_queue(event_id,building_id,captured_at,received_at,payload,status) VALUES(?,?,?,?,?,"pending")',(event_id,building_id,captured_at,datetime.datetime.now().isoformat(),json.dumps(payload)))
def sync(building_id=None):
 with offline_db() as c:
  q='SELECT event_id,building_id,captured_at,payload FROM event_queue WHERE status="pending"';params=[]
  if building_id:q+=' AND building_id=?';params=[building_id]
  pending=c.execute(q,params).fetchall()
  for event_id,bid,ts,payload in pending:
   c.execute('INSERT OR IGNORE INTO campus_events VALUES(?,?,?,?)',(event_id,bid,ts,payload));c.execute('UPDATE event_queue SET status="synced" WHERE event_id=?',(event_id,))
  return {'replayed':len(pending),'pending':c.execute('SELECT COUNT(*) FROM event_queue WHERE status="pending"').fetchone()[0],'campus_unique':c.execute('SELECT COUNT(*) FROM campus_events').fetchone()[0]}
def anomaly_actions(building):
 daily=sorted((r for r in records('daily_summary') if r['building_id']==building),key=lambda r:r['date']);actions=[]
 if len(daily)<3:return actions
 for col,unit,cause,action in [('electricity_kwh','kWh','Possible HVAC, lab equipment or extended shifts','Audit HVAC schedule, lighting and event calendar'),('water_litres','L','Possible leak, cleaning or high occupancy','Inspect taps, flow anomalies and cleaning roster')]:
  history=[numeric(r[col]) for r in daily[:-1] if numeric(r[col]) is not None];latest=numeric(daily[-1][col]);baseline=statistics.mean(history) if history else 0
  if latest is not None and baseline>0:
   excess=100*(latest-baseline)/baseline
   if excess>20:actions.append({'resource':col,'excess_pct':round(excess,1),'cause_hypothesis':cause,'recommendation':action,'evidence':f'Latest {latest:.1f} {unit} vs historical mean {baseline:.1f} {unit}','verified_cause':False})
 return sorted(actions,key=lambda a:a['excess_pct'],reverse=True)
def incentives():
 daily=records('daily_summary');by=defaultdict(list)
 for r in daily:by[r['building_id']].append(r)
 out=[]
 for bid,rows in by.items():
  rows.sort(key=lambda r:r['date']);half=len(rows)//2
  def rate(sub):return sum(numeric(r['landfill_kg'],0) for r in sub)/max(sum(numeric(r['occupancy_avg'],0) for r in sub),1)
  before=rate(rows[:half]);after=rate(rows[half:]);improvement=100*(before-after)/before if before else 0
  out.append({'building_id':bid,'baseline_kg_per_occupant_day':round(before,4),'recent_kg_per_occupant_day':round(after,4),'observed_change_pct':round(improvement,2),'ecopoints':round(max(0,improvement)*10,1),'causal_claim':'Not established: synthetic before/after data without intervention or control'})
 return sorted(out,key=lambda r:r['ecopoints'],reverse=True)
