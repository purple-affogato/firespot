<script lang="js">
    import Map from 'ol/Map.js';
    import View from 'ol/View.js';
    import KML from 'ol/format/KML.js';
    import HeatmapLayer from 'ol/layer/Heatmap.js';
    import TileLayer from 'ol/layer/Tile.js';
    import StadiaMaps from 'ol/source/StadiaMaps.js';
    import VectorSource from 'ol/source/Vector.js';


    let mapId = 20; 
    let map = null;

    const setupMap = (node) => {
        const vector = new HeatmapLayer({
          source: new VectorSource({

          })
        })

        const raster = new TileLayer({
            source: new StadiaMaps({
              layer: 'osm_bright',
            })
        })


        map = new Map({
            target: node.id,
            layers: [
                raster,
                vector
            ],
            view: new View({
                center: [0, 0],
                zoom: 2,
            })
        });
        return {
            destroy() {
                if (map) { // as Map
                    map.setTarget(null);
                    map = null;
                }
            }
        }
    }
</script>

  <div id={mapId} class="map" use:setupMap>
  </div>
  <link rel="stylesheet" href="node_modules/ol/ol.css">
  <style>
      .map {
        overflow: hidden;
        position: absolute;
        width: 100vw;
        height: 100vh;
        margin: 0;
        margin-bottom: 0;
      }
  </style>


