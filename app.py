import csv, math, statistics, html, json, os, sys, time, base64, datetime
from pathlib import Path
from collections import defaultdict, Counter
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
def load(name):
    with (DATA / (name+'.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def num(v):
    try: return float(v)
    except (ValueError, TypeError): return 0.0

st.set_page_config(page_title='ECO-GRID', page_icon='🌱', layout='wide')

# Require login before loading or displaying dashboard data.
from theme import apply_theme
from login import show_login, show_logout

DARK_MODE = apply_theme()

if not show_login():
    st.stop()

show_logout()

st.markdown("""
<div class="ecogrid-hero">
  <h1>🌱 Predictive Circular Resource Grid</h1>
  <p>Predictive Circular-Resource Grid · Smart Campus Intelligence</p>
</div>
""", unsafe_allow_html=True)
st.caption('Official supplied synthetic campus benchmark • 8 buildings • offline-capable demonstration • no pandas')
try:
    buildings=load('buildings'); daily=load('daily_summary'); hourly=load('hourly_streams'); calendar=load('calendar'); logs=load('manual_logs'); train=load('waste_events_train'); test=load('waste_events_test')
except Exception as e:
    st.error(f'Data could not be loaded: {e}'); st.stop()
ids={r['building_id']:r['building_name'] for r in buildings}
# The building photo is the background of ONLY the selection area.
# All existing metrics, charts and AI sections stay untouched.
BUILDING_PHOTOS = {
    "lab": "lab.jpg",
    "laboratory": "lab.jpg",
    "library": "library.jpg",
    "academic": "academic.jpg",
    "administration": "administration.jpg",
    "administrative": "administration.jpg",
    "hostel": "hostel.jpg",
    "cafeteria": "cafeteria.jpg",
    "canteen": "cafeteria.jpg",
}
# Optional exact-ID overrides when building names are not descriptive:
BUILDING_ID_PHOTOS = {}

# Persist the last selected building so its photograph updates on rerun.
with st.container(key="building_photo_selector"):
    selected = st.selectbox(
        "🏢 Select campus building",
        list(ids),
        format_func=lambda k: f"{k} — {ids[k]}",
        key="campus_building_selection",
    )

selected_name = ids[selected]
photo_name = BUILDING_ID_PHOTOS.get(selected)
if not photo_name:
    photo_name = next(
        (file for keyword, file in BUILDING_PHOTOS.items()
         if keyword in selected_name.lower()), None
    )
photo_path = Path(__file__).resolve().parent / "images" / photo_name if photo_name else None
if photo_path and photo_path.is_file():
    mime = "image/png" if photo_path.suffix.lower() == ".png" else "image/jpeg"
    photo_b64 = base64.b64encode(photo_path.read_bytes()).decode("ascii")
    st.markdown(f"""
    <style>
    /* Only the building selection area gets a photo background. */
    .st-key-building_photo_selector {{
        background-image:
            linear-gradient(180deg, rgba(6, 22, 32, .12) 0%,
                                   rgba(6, 22, 32, .32) 48%,
                                   rgba(6, 22, 32, .90) 100%),
            url('data:{mime};base64,{photo_b64}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        min-height: 270px;
        padding: 155px 24px 24px !important;
        border-radius: 18px;
        margin: 12px 0 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,.14);
    }}
    /* Readable label on a dark chip. */
    .st-key-building_photo_selector [data-testid="stWidgetLabel"] {{
        background: rgba(6, 22, 32, .88) !important;
        padding: 8px 12px;
        border-radius: 9px;
        width: fit-content;
        margin-bottom: 9px;
    }}
    .st-key-building_photo_selector [data-testid="stWidgetLabel"] p,
    .st-key-building_photo_selector label p {{
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,.8);
    }}
    /* Solid white selector so the building name is always visible. */
    .st-key-building_photo_selector [data-baseweb="select"] > div {{
        background: #ffffff !important;
        border: 2px solid #16a34a !important;
        border-radius: 11px !important;
        min-height: 50px;
        box-shadow: 0 3px 12px rgba(0,0,0,.18);
    }}
    .st-key-building_photo_selector [data-baseweb="select"] span,
    .st-key-building_photo_selector [data-baseweb="select"] input,
    .st-key-building_photo_selector [data-baseweb="select"] svg {{
        color: #142735 !important;
        fill: #142735 !important;
        font-weight: 750 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #142735 !important;
    }}
    /* Strong overrides for the global dark-theme text/input rules. */
    .st-key-building_photo_selector [data-testid="stWidgetLabel"],
    .st-key-building_photo_selector [data-testid="stWidgetLabel"] *,
    .st-key-building_photo_selector label,
    .st-key-building_photo_selector label * {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }}
    .st-key-building_photo_selector div[data-baseweb="select"] > div,
    .st-key-building_photo_selector [data-baseweb="select"] [role="combobox"],
    .st-key-building_photo_selector [data-baseweb="select"] [data-baseweb="input"] {{
        background-color: #ffffff !important;
        color: #102633 !important;
        -webkit-text-fill-color: #102633 !important;
        border-color: #16a34a !important;
    }}
    .st-key-building_photo_selector [data-baseweb="select"] *,
    .st-key-building_photo_selector [data-baseweb="select"] [role="combobox"] *,
    .st-key-building_photo_selector [data-baseweb="select"] [aria-selected],
    .st-key-building_photo_selector [data-baseweb="select"] input {{
        color: #102633 !important;
        -webkit-text-fill-color: #102633 !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }}
    .st-key-building_photo_selector [data-baseweb="select"] svg,
    .st-key-building_photo_selector [data-baseweb="select"] svg path {{
        fill: #102633 !important;
        color: #102633 !important;
        stroke: #102633 !important;
    }}
    /* Streamlit's selected value is rendered inside nested DIVs, not only spans.
       Override theme.py's global dark-mode color on the whole select tree. */
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"],
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] div,
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] span,
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] p,
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] input,
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] [data-testid="stMarkdownContainer"],
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
        font-weight: 750 !important;
    }}
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        background: #ffffff !important;
        border-color: #16a34a !important;
    }}
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] svg,
    .st-key-building_photo_selector [data-testid="stSelectbox"] [data-baseweb="select"] svg * {{
        color: #111827 !important;
        fill: none;
        stroke: #111827 !important;
        opacity: 1 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.caption("No photo mapped for this building yet. Add it under dashboard/images/.")

rows=sorted([r for r in hourly if r['building_id']==selected],key=lambda r:r['timestamp'])
days=sorted([r for r in daily if r['building_id']==selected],key=lambda r:r['date'])
if not rows or not days: st.error('No records for this building');st.stop()
latest=rows[-1]; lastday=days[-1]
col=st.columns(4)
col[0].metric('⚡ Last hourly electricity',f"{num(latest['electricity_kwh']):.1f} kWh")
col[1].metric('💧 Last hourly water',f"{num(latest['water_litres']):.0f} L")
col[2].metric('🗑️ Latest daily landfill',f"{num(lastday['landfill_kg']):.1f} kg")
col[3].metric('👥 Latest daily occupancy',f"{num(lastday['occupancy_avg']):.0f}")
st.caption(f"Last observed timestamp: {latest['timestamp']}. Historical benchmark, not a live meter.")

# Hour-of-day forecasting baseline; time split avoids future leakage.
cut=int(len(rows)*.8)
training=rows[:cut]; heldout=rows[cut:]
keys=[('electricity_kwh','Electricity','kWh','#ea8b18'),('water_litres','Water','L','#2588df')]
means={}; metrics={}
for key, label, unit, color in keys:
    bins=defaultdict(list)
    for r in training: bins[int(r['timestamp'][11:13])].append(num(r[key]))
    global_mean=statistics.mean(num(r[key]) for r in training)
    means[key]={h:statistics.mean(bins[h]) if bins[h] else global_mean for h in range(24)}
    errors=[abs(num(r[key])-means[key][int(r['timestamp'][11:13])]) for r in heldout]
    metrics[key]=statistics.mean(errors) if errors else 0

# Render SVG in iframe; independent of pandas, CDN and Streamlit st.html.
def graph(vals,color,unit):
    W,H=800,280; x0,y0=65,22; pw,ph=690,195; vmax=max(max(vals)*1.12,1)
    chart_bg = "#131f30" if DARK_MODE else "#ffffff"
    chart_text = "#e8f2ee" if DARK_MODE else "#34443b"
    chart_grid = "#304558" if DARK_MODE else "#dce8df"
    pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" height="280"><rect width="800" height="280" rx="14" fill="{chart_bg}"/>']
    for i in range(5):
        y=y0+ph*i/4; v=vmax*(1-i/4)
        pieces.append(f'<line x1="{x0}" y1="{y}" x2="{x0+pw}" y2="{y}" stroke="{chart_grid}"/><text x="5" y="{y+4}" font-size="12" fill="{chart_text}">{v:.1f}</text>')
    pts=[]
    for i,v in enumerate(vals):
        x=x0+pw*i/max(1,len(vals)-1);y=y0+ph*(1-v/vmax);pts.append(f'{x:.1f},{y:.1f}')
        pieces.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/><text x="{x:.1f}" y="240" text-anchor="middle" font-size="12" fill="{chart_text}">{i+1}h</text>')
    pieces.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="3"/><text x="400" y="267" text-anchor="middle" font-size="12" fill="{chart_text}">Hours ahead | {html.escape(unit)}</text></svg>')
    components.html(''.join(pieces),height=290,scrolling=False)

st.header('📈 12-hour demand forecasts')
last_hour=int(latest['timestamp'][11:13]); forecasts={}
for key,label,unit,color in keys:
    values=[means[key][(last_hour+h)%24] for h in range(1,13)]
    forecasts[key]=values
    st.subheader(f'{label} ({unit})')
    graph(values,color,unit)
    st.caption(f'Holdout MAE: {metrics[key]:.2f} {unit}. Lightweight hourly-seasonal baseline, not a trained deep-learning model.')

# Waste is measured daily in the supplied dataset, not in hourly telemetry.
st.header('🗑️ Daily waste generation')
st.caption('Actual daily records from daily_summary.csv; not an hourly waste forecast.')
waste_options = {
    'Landfill waste': ('landfill_kg', '#d97706'),
    'Wet organic waste': ('wet_organic_kg', '#16a34a'),
    'Dry recyclable waste': ('dry_recyclable_kg', '#2563eb'),
    'Composted waste': ('composted_kg', '#059669'),
    'Recycled waste': ('recycled_kg', '#7c3aed'),
}
waste_name = st.selectbox('Choose waste measurement', list(waste_options))
waste_key, waste_color = waste_options[waste_name]
waste_period = st.slider('Number of recent days', 7, min(120, len(days)), min(30, len(days)))
waste_days = days[-waste_period:]
waste_values = [num(r[waste_key]) for r in waste_days]
if waste_values:
    st.metric(f'Latest daily {waste_name.lower()}', f'{waste_values[-1]:.1f} kg')
    st.caption(f'From {waste_days[0]["date"]} to {waste_days[-1]["date"]}; horizontal axis shows days in selected period.')
    # Reuse the existing offline SVG chart, with day indices on the x-axis.
    graph(waste_values, waste_color, 'kg/day (day index)')
else:
    st.warning('No daily waste readings available for this building.')

st.header('🚨 Anomaly attribution and ranked actions')
recs=[]
for key,label,unit,color in keys:
    expected=means[key][last_hour]; observed=num(latest[key]); ratio=observed/max(expected,1)
    if ratio>1.25:
        recs.append((ratio,label,observed,expected,unit))
if recs:
    for rank,(ratio,label,obs,exp,unit) in enumerate(sorted(recs,reverse=True),1):
        st.warning(f'{rank}. {label}: {obs:.1f} {unit} vs hourly baseline {exp:.1f} {unit} ({ratio:.1f}× expected)')
        suggestion='Inspect AC, lighting and scheduled events' if label=='Electricity' else 'Check leaks, cleaning shifts and occupancy'
        st.write(f'**Why:** measured value exceeds historical hour-of-day baseline. **Action:** {suggestion}. Cause is a hypothesis, not verified causality.')
else: st.success('No latest-hour exceedance above 1.25× the seasonal baseline.')
notes=[r for r in logs if selected.lower() in (r.get('building','').lower()) or ids[selected].lower() in (r.get('building','').lower())]
st.write(f'Manual field logs available for investigation: {len(notes)} exact-name matches (aliases may require mapping).')
for r in notes[-3:]: st.caption(f"{r['logged_at']} • {r['stream']} • {r.get('note') or 'meter entry'}")

st.header('♻️ Six-class smart-bin classification')
features=['weight_g','moisture_pct','metal_signal','transparency','acoustic_hardness']
classes=sorted(set(r['category'] for r in train if r.get('category')))
# Small CPU-only nearest-centroid model with feature scaling, fitted on first 80%.
train_sorted=sorted(train,key=lambda r:r['timestamp']); split=int(len(train_sorted)*.8)
fit=train_sorted[:split]; valid=train_sorted[split:]
scales={f:max(statistics.pstdev([num(r[f]) for r in fit]),.001) for f in features}
centers={}
for c in classes:
    members=[r for r in fit if r['category']==c]
    centers[c]=[statistics.mean(num(r[f]) for r in members) / scales[f] for f in features]
def classify(row):
    vec=[num(row[f])/scales[f] for f in features]
    return min(classes,key=lambda c:sum((a-b)**2 for a,b in zip(vec,centers[c])))
correct=sum(classify(r)==r['category'] for r in valid)
accuracy=correct/max(1,len(valid))
st.metric('Time-ordered validation accuracy (baseline)',f'{accuracy:.1%}')
st.caption('CPU nearest-centroid baseline. 85% target and <2s edge latency must be tested; hidden test labels are not available.')
with st.form('bin'):
    c1,c2,c3=st.columns(3)
    weight=c1.number_input('Weight (g)',0.0,10000.0,120.0)
    moisture=c2.number_input('Moisture (%)',0.0,100.0,35.0)
    metal=c3.number_input('Metal signal',0.0,10.0,0.0)
    trans=c1.number_input('Transparency',0.0,1.0,0.3)
    acoustic=c2.number_input('Acoustic hardness',0.0,1.0,0.5)
    go=st.form_submit_button('Classify waste event')
if go:
    event=dict(zip(features,[weight,moisture,metal,trans,acoustic]))
    t0=time.perf_counter(); label=classify(event);ms=(time.perf_counter()-t0)*1000
    st.success(f'Predicted: {label} • CPU inference: {ms:.3f} ms (desktop, not edge hardware)')

st.header('🔌 Connectivity and data integrity')
delays=[r for r in rows if r['received_at']>r['timestamp']]
st.write(f'{len(delays):,} records contain a later received timestamp than capture timestamp in this building.')
st.caption('Original capture and receipt times are preserved. A real deployment requires durable local SQLite queues, event IDs, replay deduplication and synchronization tests.')
if st.button('Simulate 3-hour offline buffer and reconciliation'):
    sample=rows[-3:]; queue=[dict(r,local_event_id=f'{selected}-{r["timestamp"]}') for r in sample]
    delivered={}
    for event in queue+queue[:1]: delivered[event['local_event_id']]=event
    st.success(f'Buffered {len(queue)} readings; replayed {len(queue)+1} messages; retained {len(delivered)} unique readings after deduplication.')

st.header('🏆 EcoPoints leaderboard')
st.caption('Illustrative score: lower landfill per occupant earns more points. Not proof of behavioural change.')
rank=[]
for b in buildings:
    d=[r for r in daily if r['building_id']==b['building_id']]
    landfill=sum(num(r['landfill_kg']) for r in d)
    occupancy=sum(num(r['occupancy_avg']) for r in d)
    per_person=landfill/max(occupancy,1)
    rank.append((100/(1+per_person),b['building_name'],per_person))
for i,(score,name,rate) in enumerate(sorted(rank,reverse=True),1):
    st.write(f'{i}. **{name}** — {score:.1f} points (landfill {rate:.3f} kg/occupant-day)')
st.header('💰 Deployment and risk plan')
st.write('Target per-building prototype hardware budget: ₹12,000 (edge computer, sensors, enclosure and power). Shared server and installation excluded. Independent building gateways and a central ingestion API can scale from 3 to 30+ buildings without changing the data model.')
st.write('**Failure mitigations:** sensor drift → scheduled calibration and cross-checks; offline duplicates → unique event IDs and idempotent writes; model drift → monthly holdout evaluation and retraining; leaderboard gaming → audit against physical meters and occupancy.')
st.caption('Dataset supplied for P2P 2026 is synthetic. This application is a demonstration, not a validated production deployment.')


# =====================================
# TRAINED WASTE CLASSIFIER
# =====================================

st.divider()

st.subheader("🤖Waste Classification")

st.write(
    "Enter waste sensor readings to predict "
    "the waste category using the trained Random Forest model."
)

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.waste_predictor import load_model, predict_waste

try:
    waste_model = load_model()

    st.success("Trained waste classification model loaded!")

    st.caption(
        "Model: Pure Python Random Forest | "
        "Held-out validation accuracy: 85.35% (stratified split)"
    )

    with st.form("waste_prediction_form"):

        weight = st.number_input(
            "Weight (grams)",
            min_value=0.0,
            value=100.0
        )

        moisture = st.number_input(
            "Moisture (%)",
            min_value=0.0,
            max_value=100.0,
            value=30.0
        )

        metal = st.number_input(
            "Metal Signal",
            value=0.0
        )

        transparency = st.number_input(
            "Transparency",
            value=0.0
        )

        hardness = st.number_input(
            "Acoustic Hardness",
            value=0.0
        )

        submitted = st.form_submit_button(
            "🔍 Predict Waste Category"
        )

    if submitted:

        readings = [
            weight,
            moisture,
            metal,
            transparency,
            hardness
        ]

        predicted_category = predict_waste(
            readings,
            waste_model
        )

        st.success(f"Predicted Waste Category: {predicted_category}")
        detailed = waste_model.predict(readings)
        st.metric("Prediction confidence (not accuracy)", f"{detailed['confidence']:.2f}%")
        st.caption(f"Desktop CPU inference: {detailed['inference_ms']:.3f} ms. Probabilities are not calibrated.")

        st.info(
            "Prediction is based on the five "
            "entered sensor measurements."
        )

except FileNotFoundError:

    st.error(
        "Trained forest model not found. Verify models/waste_forest.json."
    )

except Exception as error:

    st.error(
        f"Waste classifier error: {error}"
    )


# ==========================================
# SENSOR FUSION AND OFFLINE SYNC MONITOR
# ==========================================

import json
import sqlite3
from pathlib import Path

st.divider()
st.header("🔗 Sensor Fusion & Offline Synchronization")

project_root = Path(__file__).resolve().parent.parent

fusion_report_path = (
    project_root / "models" / "sensor_fusion_report.json"
)

database_path = (
    project_root / "data" / "offline_buffer.db"
)

# SENSOR FUSION RESULTS
st.subheader("📡 Multi-Sensor Fusion")

if fusion_report_path.exists():

    with open(
        fusion_report_path,
        "r",
        encoding="utf-8"
    ) as file:
        fusion_report = json.load(file)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Fused Daily Records",
        fusion_report.get("fused_daily_records", 0)
    )

    col2.metric(
        "Delayed Sensor Readings",
        fusion_report.get("delayed_hourly_records", 0)
    )

    col3.metric(
        "Conflicting Measurements",
        fusion_report.get("conflicting_measurements", 0)
    )

    st.info(
        "Sensor fusion combines hourly meter data, "
        "daily summaries and manual observations."
    )

else:
    st.warning(
        "Sensor fusion report not found. "
        "Run src/sensor_fusion.py first."
    )

# OFFLINE SYNCHRONIZATION RESULTS
st.subheader("📴 Offline Buffering & Synchronization")

if database_path.exists():

    with sqlite3.connect(database_path) as conn:

        total = conn.execute(
            "SELECT COUNT(*) FROM readings"
        ).fetchone()[0]

        pending = conn.execute(
            "SELECT COUNT(*) FROM readings WHERE synced = 0"
        ).fetchone()[0]

        synced = conn.execute(
            "SELECT COUNT(*) FROM readings WHERE synced = 1"
        ).fetchone()[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("Buffered Records", total)
    col2.metric("Synchronized Records", synced)
    col3.metric("Pending Records", pending)

    if pending == 0:
        st.success(
            "All locally buffered records have been synchronized."
        )
    else:
        st.warning(
            f"{pending} records are waiting for synchronization."
        )

    st.caption(
        "This is a local SQLite-to-CSV synchronization "
        "demonstration, not a live cloud connection."
    )

else:
    st.warning(
        "Offline database not found. "
        "Run src/offline_sync.py first."
    )


# ==========================================
# EXPLAINABLE RESOURCE RECOMMENDATIONS
# ==========================================

import csv
from pathlib import Path
from collections import defaultdict

st.divider()
st.header("🧠 Explainable Resource Recommendations")

st.write(
    "This section identifies unusual resource consumption "
    "and explains possible causes using historical data."
)

root = Path(__file__).resolve().parent.parent
fusion_file = root / "data" / "fused_readings.csv"

if fusion_file.exists():

    with open(
        fusion_file,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        fusion_rows = list(csv.DictReader(file))

    building_ids = sorted({
        row["building_id"] for row in fusion_rows
    })

    selected_building = st.selectbox(
        "Select Building for Analysis",
        building_ids,
        key="xai_building"
    )

    building_rows = [
        row for row in fusion_rows
        if row["building_id"] == selected_building
    ]

    recommendations = []

    for resource, column, unit in [
        ("Electricity", "electricity_fused", "kWh"),
        ("Water", "water_fused", "L")
    ]:

        valid = []

        for row in building_rows:
            try:
                valid.append(
                    (row["date"], float(row[column]))
                )
            except (ValueError, KeyError):
                pass

        if len(valid) < 2:
            continue

        valid.sort(key=lambda item: item[0])

        latest_date, latest_value = valid[-1]

        historical_values = [
            value for date, value in valid[:-1]
        ]

        average = sum(historical_values) / len(
            historical_values
        )

        if average <= 0:
            continue

        difference_pct = (
            (latest_value - average) / average
        ) * 100

        st.subheader(f"{resource} Analysis")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Latest",
            f"{latest_value:.1f} {unit}"
        )

        col2.metric(
            "Historical Average",
            f"{average:.1f} {unit}"
        )

        col3.metric(
            "Difference",
            f"{difference_pct:+.1f}%"
        )

        if difference_pct > 20:

            st.warning(
                f"{resource} usage is "
                f"{difference_pct:.1f}% above its "
                "historical average."
            )

            if resource == "Electricity":
                reason = (
                    "Possible causes include increased occupancy, "
                    "extended equipment use, or inefficient AC usage."
                )
                action = (
                    "Inspect HVAC schedules, unused lights "
                    "and high-consumption equipment."
                )

            else:
                reason = (
                    "Possible causes include higher occupancy, "
                    "increased cleaning activity, or water leakage."
                )
                action = (
                    "Check water pipelines, taps and "
                    "unusual overnight water use."
                )

            st.write("**Possible causes:**", reason)
            st.info("Recommended action: " + action)

            recommendations.append({
                "resource": resource,
                "increase_pct": difference_pct,
                "action": action
            })

        else:
            st.success(
                f"{resource} usage is not more than "
                "20% above its historical average."
            )

    # Rank recommendations
    if recommendations:

        st.subheader("🎯 Ranked Recommendations")

        recommendations.sort(
            key=lambda item: item["increase_pct"],
            reverse=True
        )

        for rank, item in enumerate(
            recommendations, start=1
        ):
            st.write(
                f"**Priority {rank}: {item['resource']}** "
                f"— {item['increase_pct']:.1f}% above average"
            )
            st.write(item["action"])

    else:
        st.info(
            "No resource exceeded the 20% alert threshold."
        )

    st.caption(
        "Explanations are rule-based hypotheses, "
        "not confirmed causal diagnoses."
    )

else:
    st.warning(
        "Fused dataset not found. "
        "Run src/sensor_fusion.py first."
    )


# ==========================================
# ECOGRID - SENSOR QUALITY MONITORING
# ==========================================

import json
from pathlib import Path

st.divider()
st.header("🛡️ Sensor Quality Monitoring")

quality_root = Path(__file__).resolve().parent.parent

quality_report_file = (
    quality_root / "models/missing_sensor_report.json"
)

prediction_report_file = (
    quality_root / "models/waste_prediction_report.json"
)

if quality_report_file.exists() and prediction_report_file.exists():

    with open(
        quality_report_file,
        "r",
        encoding="utf-8"
    ) as file:
        quality_report = json.load(file)

    with open(
        prediction_report_file,
        "r",
        encoding="utf-8"
    ) as file:
        prediction_report = json.load(file)

    total = quality_report["total_test_events"]
    recovered = quality_report["events_with_missing_values"]
    original = quality_report["original_complete_events"]

    st.subheader("Sensor Data Reliability")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Events", total)
    col2.metric("Original Readings", original)
    col3.metric("Recovered Readings", recovered)

    if total > 0:
        completeness = 100 * original / total

        st.write(
            f"**Original data completeness: "
            f"{completeness:.2f}%**"
        )

        st.progress(min(1.0, max(0.0, completeness / 100)))

    st.info(
        "Missing sensor values are replaced using "
        "training-set medians. Recovered readings "
        "are flagged as lower confidence."
    )

    st.subheader("Missing Values by Sensor")

    missing_counts = quality_report.get(
        "missing_values_by_feature", {}
    )

    for sensor, count in missing_counts.items():
        st.write(f"**{sensor}:** {count} missing values")

    st.subheader("Prediction Quality")

    quality_counts = prediction_report.get(
        "prediction_quality_counts", {}
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Normal Quality",
        quality_counts.get("normal", 0)
    )

    col2.metric(
        "Lower Confidence",
        quality_counts.get("lower_confidence", 0)
    )

    st.subheader("Waste Category Distribution")

    category_counts = prediction_report.get(
        "predicted_category_counts", {}
    )

    if category_counts:
        max_count = max(category_counts.values())

        for category, count in sorted(
            category_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            st.write(f"**{category}: {count} events**")

            st.progress(
                count / max_count if max_count else 0.0
            )

    st.subheader("Classification Performance")

    col1, col2 = st.columns(2)

    col1.metric(
        "Mean Prediction Time",
        f"{prediction_report.get('mean_prediction_ms', 0)} ms"
    )

    col2.metric(
        "Maximum Prediction Time",
        f"{prediction_report.get('maximum_prediction_ms', 0)} ms"
    )

    st.caption(
        "Prediction times were measured on the "
        "development laptop. Data-quality flags "
        "are not calibrated prediction probabilities."
    )

else:
    st.warning(
        "Sensor quality reports are missing. "
        "Run recover_missing_events.py and "
        "predict_test_events.py first."
    )


# ==========================================
# CIRCULAR RESOURCE OPTIMIZATION DASHBOARD
# ==========================================

import csv
from pathlib import Path

st.divider()
st.header("♻️ Circular Resource Optimization")

circular_root = Path(__file__).resolve().parent.parent

recommendations_path = (
    circular_root / "data" / "circular_recommendations.csv"
)

leaderboard_path = (
    circular_root / "data" / "ecopoints_leaderboard.csv"
)


def load_circular_csv(path):
    with open(
        path,
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


if recommendations_path.exists() and leaderboard_path.exists():

    recommendations_data = load_circular_csv(
        recommendations_path
    )

    leaderboard_data = load_circular_csv(
        leaderboard_path
    )

    # ======================================
    # BUILDING SELECTOR
    # ======================================

    building_options = sorted({
        row["building_id"]
        for row in recommendations_data
    })

    selected_circular_building = st.selectbox(
        "Select Building for Resource Optimization",
        building_options,
        key="circular_building_selector"
    )

    building_recommendations = [
        row for row in recommendations_data
        if row["building_id"] == selected_circular_building
    ]

    # ======================================
    # RESOURCE SAVINGS
    # ======================================

    st.subheader("Potential Resource Savings")

    cols = st.columns(3)

    for index, row in enumerate(building_recommendations):

        with cols[index % 3]:

            resource = row["resource"].title()
            saving = float(row["estimated_saving"])
            unit = row["unit"]

            st.metric(
                resource,
                f"{saving:,.1f} {unit}"
            )

    st.caption(
        "Values are illustrative reduction scenarios "
        "calculated from historical totals, not "
        "verified savings."
    )

    # ======================================
    # RECOMMENDED ACTIONS
    # ======================================

    st.subheader("Recommended Sustainability Actions")

    for row in building_recommendations:

        st.write(
            f"**{row['resource'].title()}**"
        )

        st.write(row["recommendation"])

        st.caption(
            f"Assumption: {row['assumption']}"
        )

    # ======================================
    # ECOPOINTS LEADERBOARD
    # ======================================

    st.subheader("🏆 EcoPoints Leaderboard")

    sorted_leaderboard = sorted(
        leaderboard_data,
        key=lambda row: float(row["ecopoints"]),
        reverse=True
    )

    for row in sorted_leaderboard:

        rank = row["rank"]
        building = row["building_id"]
        points = float(row["ecopoints"])

        st.write(
            f"**#{rank} — {building}**: "
            f"{points:,.1f} EcoPoints"
        )

    if sorted_leaderboard:

        winner = sorted_leaderboard[0]

        st.success(
            f"🏆 Current EcoPoints Leader: "
            f"{winner['building_id']} "
            f"({float(winner['ecopoints']):,.1f} points)"
        )

    st.caption(
        "EcoPoints are an illustrative scoring "
        "system based on recycling, composting "
        "and solar generation. They are not "
        "redeemable rewards."
    )

else:

    st.warning(
        "Circular optimization reports not found. "
        "Run src/circular_optimizer.py first."
    )



# ================================================================
# JUDGES' TESTING PANEL — real per-case correctness and accuracy
# Uses the SAME trained KNN backend as the waste prediction form.
# ================================================================
import io
st.divider()
st.header("🧪 Judges' Waste Classification Testing")
st.caption("For each case, the model predicts a category. Accuracy requires the actual correct category; a single labeled case is either correct or incorrect.")

if "judge_test_results" not in st.session_state:
    st.session_state["judge_test_results"] = []

try:
    # Use the trained model already loaded by the existing dashboard.
    judge_model = waste_model if "waste_model" in globals() else load_model()
    judge_categories = sorted(set(str(r["category"]) for r in train if r.get("category")))

    with st.form("judge_manual_test_form"):
        st.subheader("Test one event")
        event_id = st.text_input("Test case ID (optional)", value="")
        j1, j2, j3 = st.columns(3)
        j_weight = j1.number_input("Test weight (g)", min_value=0.0, value=100.0, key="judge_weight")
        j_moisture = j2.number_input("Test moisture (%)", min_value=0.0, max_value=100.0, value=30.0, key="judge_moisture")
        j_metal = j3.number_input("Test metal signal", min_value=0.0, value=0.0, key="judge_metal")
        j_transparency = j1.number_input("Test transparency", min_value=0.0, max_value=1.0, value=0.3, key="judge_transparency")
        j_hardness = j2.number_input("Test acoustic hardness", min_value=0.0, max_value=1.0, value=0.5, key="judge_hardness")
        actual_option = st.selectbox("Actual category (optional; choose if judge knows the correct answer)", ["Unknown / not provided"] + judge_categories)
        judge_submit = st.form_submit_button("🔍 Predict and evaluate")

    if judge_submit:
        t_start = time.perf_counter()
        j_pred = str(predict_waste([j_weight, j_moisture, j_metal, j_transparency, j_hardness], judge_model))
        j_ms = (time.perf_counter() - t_start) * 1000
        j_actual = "" if actual_option == "Unknown / not provided" else actual_option
        j_result = "Not verifiable" if not j_actual else ("Correct" if j_pred == j_actual else "Incorrect")
        st.session_state["judge_test_results"].append({
            "event_id": event_id.strip() or f"Manual-{len(st.session_state['judge_test_results']) + 1}",
            "predicted_category": j_pred, "confidence_pct": judge_detail["confidence"], "actual_category": j_actual,
            "result": j_result, "inference_ms": round(j_ms, 3),
        })
        st.success(f"Predicted category: {j_pred}")
        judge_detail = judge_model.predict([j_weight,j_moisture,j_metal,j_transparency,j_hardness])
        st.metric("This case: prediction confidence (not accuracy)",f"{judge_detail['confidence']:.2f}%")
        if j_actual:
            (st.success if j_result == "Correct" else st.error)(f"This case: {j_result} (actual: {j_actual})")
        else:
            st.info("Actual label was not provided, so this case has no measurable accuracy. The confidence is not the same as accuracy.")

    st.subheader("Test multiple cases")
    st.caption("Upload a CSV with weight_g, moisture_pct, metal_signal, transparency, acoustic_hardness. Include a 'category' column for accuracy; otherwise predictions only. Optional event_id column.")
    uploaded_tests = st.file_uploader("Upload test cases (CSV)", type=["csv"], key="judge_test_csv")
    if uploaded_tests is not None and st.button("▶ Run uploaded test cases", key="judge_run_bulk"):
        import io
        try:
            bulk_rows = list(csv.DictReader(io.StringIO(uploaded_tests.getvalue().decode("utf-8-sig"))))
            needed = ["weight_g", "moisture_pct", "metal_signal", "transparency", "acoustic_hardness"]
            if not bulk_rows:
                st.warning("The CSV has no test rows.")
            elif not set(needed).issubset(set(bulk_rows[0])):
                st.error("CSV must contain: " + ", ".join(needed))
            else:
                predictions = []
                for idx, r in enumerate(bulk_rows, 1):
                    try:
                        readings = [float(r[f]) for f in needed]
                        detail = judge_model.predict(readings)
                        pred = detail["category"]
                        actual = (r.get("category") or "").strip()
                        result = "Not verifiable" if not actual else ("Correct" if pred == actual else "Incorrect")
                        predictions.append({"event_id": r.get("event_id") or f"Row-{idx}",
                                            "predicted_category": pred, "confidence_pct": detail["confidence"], "actual_category": actual, "result": result})
                    except (TypeError, ValueError, KeyError) as exc:
                        predictions.append({"event_id": r.get("event_id") or f"Row-{idx}",
                                            "predicted_category": "", "confidence_pct": "", "actual_category": "", "result": f"Invalid input: {exc}"})
                st.session_state["judge_test_results"].extend(predictions)
                st.success(f"Processed {len(predictions):,} rows. Predictions are listed below.")
        except (UnicodeDecodeError, csv.Error) as exc:
            st.error(f"Could not read CSV: {exc}")

    results = st.session_state["judge_test_results"]
    if results:
        labeled = [r for r in results if r["result"] in ("Correct", "Incorrect")]
        correct_count = sum(r["result"] == "Correct" for r in labeled)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cases tested", len(results))
        m2.metric("Labeled cases", len(labeled))
        m3.metric("Correct predictions", correct_count)
        m4.metric("Overall test accuracy", f"{correct_count / len(labeled):.2%}" if labeled else "N/A")
        if not labeled:
            st.info("No ground-truth categories provided. Per-case predictions are available, but accuracy cannot be calculated.")
        st.dataframe(results, use_container_width=True, hide_index=True)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["event_id", "predicted_category", "confidence_pct", "actual_category", "result", "inference_ms"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
        st.download_button("⬇ Download test results CSV", output.getvalue().encode("utf-8"),
                           file_name="ecogrid_judges_test_results.csv", mime="text/csv")
        if st.button("Clear testing results", key="judge_clear_results"):
            st.session_state["judge_test_results"] = []
            st.rerun()
except Exception as judge_error:
    st.error(f"Testing panel cannot load the trained Random Forest model: {judge_error}")
    st.info("Make sure src/waste_predictor.py and models/waste_forest.json are present.")

# =========================================================
# VERIFIED REQUIREMENTS MODULES (standard-library backend)
# =========================================================
from src.ecogrid_engine import WasteForest, evaluate, fuse_daily, forecast, enqueue, sync, offline_db, anomaly_actions, incentives, records

st.divider()
st.header("🔬 Verified AI and Campus Operations")
st.caption("All calculations use the supplied synthetic dataset. Hardware, live camera, and real-world incentive effects require separate field tests.")
with st.expander("📊 Validated model performance and confusion matrix", expanded=True):
    report_file=ROOT / 'reports' / 'validation_report.json'
    if report_file.exists():
        vr=json.loads(report_file.read_text())
        a,b,c=st.columns(3)
        a.metric("Held-out validation accuracy",f"{100*vr['validation_accuracy']:.2f}%")
        b.metric("Validation examples",vr['validation_count'])
        c.metric("Waste categories",len(vr['classes']))
        st.caption("Model was trained on the other 80% for this validation. The deployed model was subsequently refitted on all labeled training examples. Hidden test accuracy remains unknown.")
        st.write("**Confusion matrix** (rows = actual, columns = predicted)")
        st.dataframe([dict(actual=vr['classes'][i],**{vr['classes'][j]:n for j,n in enumerate(row)}) for i,row in enumerate(vr['confusion_matrix'])],hide_index=True)
        st.write("**Precision, recall and F1 by class**")
        st.dataframe([{'category':k,'precision':round(v['precision'],3),'recall':round(v['recall'],3),'f1':round(v['f1-score'],3)} for k,v in vr['classification_report'].items() if isinstance(v,dict) and k in vr['classes']],hide_index=True)

with st.expander("📡 Multi-modal sensor fusion, missing data and conflicting readings"):
    fused,fs=fuse_daily()
    c1,c2,c3=st.columns(3)
    c1.metric("Fused daily records",fs['records']);c2.metric("Conflicting sensor totals",fs['conflicts']);c3.metric("Input source types",fs['source_types'])
    st.caption(fs['note'])
    st.dataframe([r for r in fused if r['building_id']==selected][-12:],hide_index=True)
    st.download_button("Download fused readings",'\n'.join([','.join(fused[0].keys())]+[','.join(str(v) for v in row.values()) for row in fused]),'fused_readings.csv','text/csv')

with st.expander("⏱️ Forecast quality and edge compute trade-off"):
    for resource in ('electricity_kwh','water_litres'):
        fc=forecast(selected,resource)
        st.write(f"**{resource}:** 12-hour predictions: {fc['next_12_hours']}")
        st.caption(f"Holdout MAE: {fc['holdout_mae']} | {fc['tradeoff']}")
    st.caption("Model inference latency shown above is desktop CPU latency. Verify <2 seconds on actual target hardware before claiming edge compliance.")

with st.expander("📴 Durable offline event queue and idempotent reconciliation"):
    with st.form('real_offline_queue'):
        offline_id=st.text_input('Unique event ID',value=f'{selected}-DEMO-001')
        offline_val=st.number_input('Electricity reading (kWh)',min_value=0.0,value=5.0)
        offline_add=st.form_submit_button('Queue offline reading')
    if offline_add:
        enqueue(offline_id,selected,datetime.datetime.now().isoformat(),{'electricity_kwh':offline_val})
        st.success('Event stored durably in SQLite (duplicate IDs ignored).')
    if st.button('Reconnect and reconcile',key='real_sync'):
        st.json(sync(selected))
    with offline_db() as con:
        st.metric('Pending queue events',con.execute('SELECT COUNT(*) FROM event_queue WHERE status="pending"').fetchone()[0])
        st.metric('Campus-wide unique events',con.execute('SELECT COUNT(*) FROM campus_events').fetchone()[0])
    st.caption('Demo persists events locally. This is not a live distributed gateway-to-cloud integration.')

with st.expander("🧠 Ranked root-cause hypotheses and evidence"):
    actions=anomaly_actions(selected)
    if actions:
        for i,a in enumerate(actions,1):
            st.warning(f"Priority {i}: {a['resource']} (+{a['excess_pct']}%)")
            st.write('Evidence:',a['evidence'],'| Possible cause:',a['cause_hypothesis'])
            st.info(a['recommendation'])
    else:st.success('No recent daily anomaly above 20% of historical mean.')
    st.caption('These are explainable hypotheses; causal confirmation requires logs and inspection.')

with st.expander("🏆 Measurable EcoPoints incentive loop"):
    score=incentives();st.dataframe(score,hide_index=True)
    st.caption('Before/after occupancy-normalized landfill is measured. The supplied synthetic data do not prove an incentive caused the change. A real intervention needs control buildings and a pre/post study.')

with st.expander("💰 Cost, 30-building scale and failure-mode mitigations"):
    budget=[('Low-cost edge computer',4200),('Electricity metering interface',1800),('Water flow meter',1300),('Bin load cell + amplifier',1100),('Moisture/metal/optical sensors',1500),('Connectivity module',700),('Power + enclosure + cabling',1400)]
    st.dataframe([{'component':k,'estimated_INR':v} for k,v in budget],hide_index=True)
    st.metric('Estimated per-building hardware total',f"₹{sum(v for _,v in budget):,}")
    st.write('3 buildings → independent edge queues → one central ingestion/database service; 30+ buildings → same event schema and per-building partitioning, with batching and capacity monitoring. No redesign required conceptually; throughput/load testing is still needed.')
    st.write('**Sensor drift:** periodic calibration and cross-checks. **Offline duplicates:** unique IDs and SQLite transactions. **Model drift:** monitor labeled holdout performance and retrain. **Leaderboard gaming:** audit physical readings and normalize by occupancy.')
    st.caption('Budget is an engineering estimate, not supplier quotes. Cameras, installation, taxes and shared server are not included; adding a camera requires a revised cost envelope.')
