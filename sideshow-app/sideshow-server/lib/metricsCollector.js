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

    parse(stdout.trim(), { columns: true, skip_lines_with_error: true }, (parseError, parsed) => {
      if (parseError) {
        return cb(parseError, null);
      }

      console.dir(parsed);

      const cpu = parsed.find(metricsEntry => metricsEntry['Name'] === 'CPU Package' && metricsEntry['SensorType'] === 'Temperature');
      const gpu = parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Core' && metricsEntry['SensorType'] === 'Temperature');

      cb(null, {cpu: cpu.Value, gpu: gpu.Value});
    });
  });
}

module.exports = {
  getMetrics
};