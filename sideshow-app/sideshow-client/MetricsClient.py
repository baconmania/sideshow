import requests

def get_metrics():
  return requests.get('http://baconmania.cc:9000/metrics', timeout=1).json()