// terrain.js — SRTM elevation + slope for the India study chips.
// Dataset: USGS/SRTMGL1_003 (30 m, void-filled). Slope via ee.Terrain.slope (degrees).

var aoi = ee.Geometry.MultiPoint([
  [93.0683, 26.2394], [93.8042, 26.4234], [92.9304, 26.6074]
]).bounds().buffer(5000);

var srtm = ee.Image('USGS/SRTMGL1_003').select('elevation');  // metres
var slope = ee.Terrain.slope(srtm).rename('slope');           // degrees

Map.centerObject(aoi, 9);
Map.addLayer(srtm.clip(aoi), {min: 0, max: 800, palette: ['green', 'yellow', 'brown', 'white']}, 'SRTM elevation (m)');
Map.addLayer(slope.clip(aoi), {min: 0, max: 30, palette: ['white', 'orange', 'red']}, 'Slope (deg)');
print('Elevation stats (m):', srtm.reduceRegion({
  reducer: ee.Reducer.minMax().combine(ee.Reducer.mean(), '', true),
  geometry: aoi, scale: 30, maxPixels: 1e9
}));
