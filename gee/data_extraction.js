// data_extraction.js — join rainfall + terrain + Sentinel indices, preview samples.
// Requires rainfall.js / terrain.js / sentinel_features.js layers defined above
// (paste those blocks first, or replicate the few lines here).

var chips = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Rectangle([93.0453, 26.2164, 93.0913, 26.2624]), {chip: 'India_1072277'}),
  ee.Feature(ee.Geometry.Rectangle([93.7812, 26.4004, 93.8272, 26.4464]), {chip: 'India_981708'}),
  ee.Feature(ee.Geometry.Rectangle([92.9074, 26.5844, 92.9534, 26.6304]), {chip: 'India_591317'})
]);

var stacked = rainSum.addBands([rainMax, srtm, slope, ndvi, ndwi, ndbi]);
print('Stacked bands:', stacked.bandNames());

var grid = ee.FeatureCollection.randomPoints(chips.geometry(), 1500, 42);
var sampled = stacked.sampleRegions({
  collection: grid, properties: [], scale: 30, geometries: true
});
print('Sampled features:', sampled.size());
print(sampled.limit(5));
Map.addLayer(sampled.draw('red'), {}, 'sample points');
