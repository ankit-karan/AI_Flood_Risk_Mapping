// sentinel_features.js — cloud-masked Sentinel-2 NDVI/NDWI/NDBI.
// Collection: COPERNICUS/S2_SR_HARMONIZED (surface reflectance x10000).
// Window 2016-08-01 → 2016-08-20 (monsoon: least-cloudy composite). B8=10m.

function maskS2(img) {
  var scl = img.select('SCL');
  // Keep vegetation, bare soil, water, snow; drop cloud/shadow/cirrus classes.
  var good = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7)).or(scl.eq(11));
  return img.updateMask(good);
}

var aoi = ee.Geometry.MultiPoint([
  [93.0683, 26.2394], [93.8042, 26.4234], [92.9304, 26.6074]
]).bounds().buffer(5000);

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterDate('2016-08-01', '2016-08-21')
  .filterBounds(aoi)
  .map(maskS2);

var composite = s2.median();  // monsoon-season median composite
var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
var ndwi = composite.normalizedDifference(['B3', 'B8']).rename('NDWI');
var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');

Map.centerObject(aoi, 9);
Map.addLayer(ndvi.clip(aoi), {min: -0.2, max: 0.9, palette: ['brown', 'yellow', 'green']}, 'NDVI');
Map.addLayer(ndwi.clip(aoi), {min: -0.5, max: 0.5, palette: ['brown', 'white', 'blue']}, 'NDWI');
Map.addLayer(ndbi.clip(aoi), {min: -0.5, max: 0.5, palette: ['blue', 'white', 'grey']}, 'NDBI');
print('S2 usable images in window:', s2.size());
