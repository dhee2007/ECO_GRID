from ecogrid_engine import *
model=WasteForest();rows,summary=evaluate(model,records('waste_events_test'))
with (ROOT/'reports/test_predictions.csv').open('w',newline='',encoding='utf-8') as f:
 writer=csv.DictWriter(f,fieldnames=['event_id','building_id','prediction','confidence_pct','inference_ms','actual_category','correct','imputed_features']);writer.writeheader();writer.writerows(rows)
print(summary)
