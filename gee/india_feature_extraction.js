// india_feature_extraction.js — India-lattice environmental features in GEE.
// Reference-week rainfall (same window as the Assam training event) plus
// terrain + Sentinel-2 composite; export with export_features.js pattern.

var indiaBox = ee.Geometry.Rectangle([68.0, 6.0, 98.0, 36.0]);

var rain = ee.ImageCollection('NASA/GPM_L3/IMERG_V07')
  .filterDate('2016-08-05', '2016-08-13').select('precipitation');
var rainSum = rain.sum().multiply(0.5).rename('rainfall_sum');
var rainMax = rain.max().rename('rainfall_max');
var rainMean = rain.mean().multiply(0.5).rename('rainfall_mean');

var srtm = ee.Image('USGS/SRTMGL1_003').select('elevation');
var slope = ee.Terrain.slope(srtm);

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(indiaBox).filterDate('2016-08-01', '2016-08-21')
  .map(function(img) {
    var scl = img.select('SCL');
    return img.updateMask(
      scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7)).or(scl.eq(11)));
  }).median();
var ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI');
var ndwi = s2.normalizedDifference(['B3', 'B8']).rename('NDWI');
var ndbi = s2.normalizedDifference(['B11', 'B8']).rename('NDBI');

var indiaStack = rainSum.addBands([rainMean, rainMax, srtm, slope, ndvi, ndwi, ndbi]);
print('India stack bands:', indiaStack.bandNames());
Map.addLayer(rainSum.clip(indiaBox),
  {min: 0, max: 300, palette: ['white', 'blue', 'darkblue']}, 'IMERG week sum');
Map.centerObject(indiaBox, 5);
