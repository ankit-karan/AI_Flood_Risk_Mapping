// india_grid.js — whole-India prediction lattice in Earth Engine.
// 0.1° (~11 km) grid over the GADM India extent (lon 68–98, lat 6–36),
// kept honest: IMERG rain is 0.1°, SRTM 30 m, S2 10–20 m (see other scripts).

var indiaBox = ee.Geometry.Rectangle([68.0, 6.0, 98.0, 36.0]);
var grid = ee.FeatureCollection(
  ee.List.sequence(68.0, 97.9, 0.1).map(function(lon) {
    return ee.List.sequence(6.0, 35.9, 0.1).map(function(lat) {
      return ee.Feature(ee.Geometry.Point([lon, lat]),
        {grid_lon: lon, grid_lat: lat});
    });
  }).flatten()
);
// NOTE: mask `grid` to the GADM/GAUL India boundary in the Code Editor
// (Imports -> FAO GAUL level-0 -> filter NAME_0 == 'India' -> filterBounds)
// before sampling/exporting, mirroring src/india_grid.py.
print('India lattice cells (pre-mask):', grid.size());
Map.addLayer(indiaBox, {}, 'India bbox');
Map.centerObject(indiaBox, 5);
