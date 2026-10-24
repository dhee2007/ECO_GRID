from .ecogrid_engine import WasteForest

def load_model():return WasteForest()
def predict_waste(readings,model):return model.predict(readings)['category']
