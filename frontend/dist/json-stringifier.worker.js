self.onmessage = function(event) {
  try {
    const dataObject = event.data;
    const jsonString = JSON.stringify(dataObject);
    self.postMessage(jsonString);

  } catch (error) {
    console.error('Worker failed to stringify JSON:', error);
  }
};