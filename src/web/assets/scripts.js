const NUM_OF_CHANNELS_TO_DISPLAY = 3;

function updateTempDisplays(json) {
  
  for (let i = 0; i < NUM_OF_CHANNELS_TO_DISPLAY; i++) {
    let temp_c = parseFloat(json[i]["temperature_C"]).toFixed(2);


    document.getElementById(`tempdisplay-temp${i+1}`).innerHTML = temp_c + "°C";
    document.getElementById(`tempdisplay-title${i+1}`).innerHTML = json[i]["verbose_name"];
    document.getElementById(`tempdisplay-probe${i+1}`).innerHTML = json[i]["probe"];

  }

}


function updateTable(json) {
  for (let i = 0; i < NUM_OF_CHANNELS_TO_DISPLAY; i++) {
    document.getElementById(`channel${i+1}`).innerHTML = json[i]["_name"];
    document.getElementById(`probe${i+1}`).innerHTML = json[i]["probe"];
    document.getElementById(`tempc${i+1}`).innerHTML = parseFloat(json[i]["temperature_C"]).toFixed(3);
    document.getElementById(`tempf${i+1}`).innerHTML = parseFloat(json[i]["temperature_F"]).toFixed(3);
    document.getElementById(`tempk${i+1}`).innerHTML = parseFloat(json[i]["temperature_K"]).toFixed(3);
    document.getElementById(`resistance${i+1}`).innerHTML = parseFloat(json[i]["resistance_Om"]).toFixed(3);
  }
}





function updateMeasurementValues(json) {
  console.log(json);

  updateTempDisplays(json);
  updateTable(json);
}



async function getApiResponseAndUpdate() {
    const url = "/api/measurements/list";
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
  
      const json = await response.json();
      updateMeasurementValues(json);
    } catch (error) {
      console.error(error.message);
    }
  }
  



var startLiveUpdate = function () {
    if (document.querySelector('#interval_onoff_input').checked) {
      getApiResponseAndUpdate();
    }

    setTimeout(startLiveUpdate, interval)
};


var interval = 2500;

document.addEventListener("DOMContentLoaded", function() {

  var interval_input_el = document.getElementById("interval_input")
  
  interval_input_el.addEventListener("change", function() {
    interval = parseInt(interval_input_el.value);
    console.log(interval);
  });

  getApiResponseAndUpdate();
  setTimeout(startLiveUpdate, interval);
}); 
