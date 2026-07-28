import importlib, sys
sys.path.append('.')
try:
    app = importlib.import_module('app')
    print('Imported app')
    resp = app.generate_assistant_response('Say hello from Gemini test')
    print('Response:', resp)
except Exception as e:
    print('ERROR', e)
