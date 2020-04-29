const { exec } = require('child_process');
const parse = require('csv-parse');

const getMetrics = function (cb) {
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

      const cpuTemp = +parsed.find(metricsEntry => metricsEntry['Name'] === 'CPU Package' && metricsEntry['SensorType'] === 'Temperature').Value;
      const gpuTemp = +parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Core' && metricsEntry['SensorType'] === 'Temperature').Value;

      const cpuLoads = parsed
        .filter(metricsEntry => metricsEntry['Name'].startsWith('CPU Core') && metricsEntry['SensorType'] === 'Load')
        .sort(metricsEntry => Number.parseInt(metricsEntry['Name'].match(/\d/)[0]))
        .map(metricsEntry => {
          return { load: +metricsEntry['Value'] };
        });
      const gpuCoreLoad = +parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Core' && metricsEntry['SensorType'] === 'Load').Value;
      const gpuEngineLoad = +parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Video Engine' && metricsEntry['SensorType'] === 'Load').Value;
      const gpuMemoryUsed = +parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Memory Used' && metricsEntry['SensorType'] === 'SmallData').Value;
      const gpuMemoryTotal = +parsed.find(metricsEntry => metricsEntry['Name'] === 'GPU Memory Total' && metricsEntry['SensorType'] === 'SmallData').Value;

      cb(null, { 
        temps: {
          cpu: cpuTemp, gpu: gpuTemp
        },
        load: {
          cpu: cpuLoads, gpuCore: gpuCoreLoad, gpuRenderingEngine: gpuEngineLoad
        },
        memory: {
          gpuUsed: gpuMemoryUsed,
          gpuTotal: gpuMemoryTotal
        }
      });
    });
  });
}

module.exports = {
  getMetrics
};