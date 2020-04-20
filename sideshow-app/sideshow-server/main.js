const express = require('express');
const metricsCollector = require('./lib/metricsCollector');

const app = express();
const port = 9000;

app.get('/metrics', (req, res) => {
  metricsCollector.getMetrics((err, metrics) => {
    if (err) {
      return res.status(500).send(err);
    }

    return res.send(metrics);
  });
});

app.listen(port, () => console.log("sideshow server listening on ${port}"));