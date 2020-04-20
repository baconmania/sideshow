const { exec } = require('child_process');
const parse = require('csv-parse');

const getMetrics = function(cb) {
  exec("wmic.exe '/NAMESPACE:\\\\root\\OpenHardwareMonitor' /NODE:'localhost' path Sensor get /FORMAT:CSV", (error, stdout, stderr) => {
    if (error) {
      cb(Error(error), null);
    }

    if (stderr) {
      console.log(`stderr: ${stderr}`);
      return;
    }

    const parsed = parse(stdout);
    console.log(`parsed: ${parsed}`);

    const cpuTemp = parsed.find(metricsEntry => metricsEntry['Name'] === 'CPU Package' && metricsEntry['SensorType'] === 'Temperature');
    const gpuTemp = parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Core' && metricsEntry['SensorType'] === 'Temperature');

    cb(null, {cpuTemp, gpuTemp});
  });
}

module.exports = {
  getMetrics
};