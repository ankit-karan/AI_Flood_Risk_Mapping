// training_feature_extraction.js — label-joined training features in GEE.
// Joins Sen1Floods11 chip bounds with IMERG + SRTM + Sentinel-2 layers.
// (Chip bounds below are the STAC bboxes; labels themselves stay in COGs and
// are joined to the sampled table offline via row/col, exactly as
// src/spatial_sampling.py does.)

var chips = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Rectangle([93.0453, 26.2164, 93.0913, 26.2624]),
    {chip: 'India_1072277', rain_start: '2016-08-05', rain_end: '2016-08-13'}),
  ee.Feature(ee.Geometry.Rectangle([93.7812, 26.4004, 93.8272, 26.4464]),
    {chip: 'India_981708', rain_start: '2016-08-05', rain_end: '2016-08-13'}),
  ee.Feature(ee.Geometry.Rectangle([92.9074, 26.5844, 92.9534, 26.6304]),
    {chip: 'India_591317', rain_start: '2016-08-05', rain_end: '2016-08-13'}),
  ee.Feature(ee.Geometry.Rectangle([81.4549, 7.9569, 81.5009, 8.0029]),
    {chip: 'Sri-Lanka_551926', rain_start: '2017-05-23', rain_end: '2017-05-31'}),
  ee.Feature(ee.Geometry.Rectangle([81.0410, 7.6350, 81.0870, 7.6810]),
    {chip: 'Sri-Lanka_120804', rain_start: '2017-05-23', rain_end: '2017-05-31'}),
  ee.Feature(ee.Geometry.Rectangle([81.0870, 7.8189, 81.1330, 7.8649]),
    {chip: 'Sri-Lanka_233609', rain_start: '2017-05-23', rain_end: '2017-05-31'})
]);

var srtm = ee.Image('USGS/SRTMGL1_003').select('elevation');
var slope = ee.Terrain.slope(srtm);

function chipFeatures(chip) {
  var geom = chip.geometry();
  var rain = ee.ImageCollection('NASA/GPM_L3/IMERG_V07')
    .filterDate(chip.get('rain_start'), chip.get('rain_end'))
    .select('precipitation');
  var rainSum = rain.sum().multiply(0.5).rename('rainfall_sum');
  var rainMax = rain.max().rename('rainfall_max');
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(geom)
    .filterDate('2016-08-01', '2017-06-30')
    .map(function(img) {
      var scl = img.select('SCL');
      var good = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7)).or(scl.eq(11));
      return img.updateMask(good);
    }).median();
  var ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI');
  var ndwi = s2.normalizedDifference(['B3', 'B8']).rename('NDWI');
  var ndbi = s2.normalizedDifference(['B11', 'B8']).rename('NDBI');
  var stacked = rainSum.addBands([rainMax, srtm, slope, ndvi, ndwi, ndbi]);
  var pts = ee.FeatureCollection.randomPoints(geom, 1500, 42);
  return stacked.sampleRegions({collection: pts, scale: 30, geometries: true})
    .map(function(f) { return f.set('chip', chip.get('chip')); });
}

var training = chips.map(chipFeatures).flatten();
print('GEE training sample count:', training.size());
