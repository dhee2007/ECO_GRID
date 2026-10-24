from ecogrid_engine import *
import time,json,statistics
m=WasteForest();train=records('waste_events_train');test=records('waste_events_test')
assert len(m.classes)>=5
p=m.predict([5,0,0,.19,.63]);assert p['category'] in m.classes
result,summary=evaluate(m,test);assert len(result)==len(test)
assert summary['accuracy_pct'] is None
fused,stats=fuse_daily();assert len(fused)>0
buildings=records('buildings');bid=buildings[0]['building_id']
forecast(bid);anomaly_actions(bid);incentives()
key='offline-test-'+str(int(time.time()))
enqueue(key,bid,'2026-06-20T10:00:00',{'electricity_kwh':5});enqueue(key,bid,'2026-06-20T10:00:00',{'electricity_kwh':5})
first=sync(bid);second=sync(bid);assert second['replayed']==0
samples=[m.predict([5,0,0,.19,.63])['inference_ms'] for _ in range(20)]
report={'tests':'passed','test_rows':len(test),'hidden_test_accuracy':'unavailable (no labels)','model_classes':m.classes,'median_desktop_inference_ms':statistics.median(samples),'p95_desktop_inference_ms':sorted(samples)[18],'fusion':stats,'offline_first_sync':first,'offline_second_sync':second,'hardware_tested':False}
(ROOT/'reports/system_test_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
