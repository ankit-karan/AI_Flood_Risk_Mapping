// rainfall.js — NASA GPM IMERG V07 accumulated rainfall, India event window.
// Run in https://code.earthengine.google.com/
// Study area chips (Sen1Floods11 India, 2016-08-12); window 2016-08-05 → 2016-08-12.

var chips = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Rectangle([93.0453, 26.2164, 93.0913, 26.2624]), {chip: 'India_1072277'}),
  ee.Feature(ee.Geometry.Rectangle([93.7812, 26.4004, 93.8272, 26.4464]), {chip: 'India_981708'}),
  ee.Feature(ee.Geometry.Rectangle([92.9074, 26.5844, 92.9534, 26.6304]), {chip: 'India_591317'})
]);
var aoi = chips.geometry();

var imerg = ee.ImageCollection('NASA/GPM_L3/IMERG_V07')
  .filterDate('2016-08-05', '2016-08-13')  // end-exclusive: covers 05→12 Aug
  .select('precipitation');                // mm/hr, 0.1 deg, 30-min cadence

// Accumulated rainfall (mm) over the 8-day pre-event window.
var rainSum = imerg.sum().multiply(0.5).rename('rainfall_sum');
// Peak 30-min intensity (mm/hr) in the window.
var rainMax = imerg.max().rename('rainfall_max');

Map.centerObject(aoi, 10);
Map.addLayer(rainSum.clip(aoi), {min: 0, max: 300, palette: ['white', 'blue', 'darkblue']}, 'IMERG 8-day accumulation (mm)');
print('IMERG image count in window:', imerg.size());
print('Mean accumulated rainfall (mm):', rainSum.reduceRegion({
  reducer: ee.Reducer.mean(), geometry: aoi, scale: 11132, maxPixels: 1e9
}));
