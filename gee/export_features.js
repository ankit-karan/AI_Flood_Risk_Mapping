// export_features.js — export the sampled feature table to Google Drive.
// After running, download the CSV to data/real/gee_export_features.csv
// (scripts/run_real_pipeline.py prefers it automatically).

var chips = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Rectangle([93.0453, 26.2164, 93.0913, 26.2624]), {chip: 'India_1072277'}),
  ee.Feature(ee.Geometry.Rectangle([93.7812, 26.4004, 93.8272, 26.4464]), {chip: 'India_981708'}),
  ee.Feature(ee.Geometry.Rectangle([92.9074, 26.5844, 92.9534, 26.6304]), {chip: 'India_591317'})
]);

var stacked = rainSum.addBands([rainMax, srtm, slope, ndvi, ndwi, ndbi]);
var grid = ee.FeatureCollection.randomPoints(chips.geometry(), 1500, 42);
var sampled = stacked.sampleRegions({
  collection: grid, scale: 30, geometries: true
});

Export.table.toDrive({
  collection: sampled,
  description: 'REAL_FLOOD_FEATURES_India2016',
  fileFormat: 'CSV'
});
print('Export started — check Tasks tab, then move CSV to data/real/gee_export_features.csv');
