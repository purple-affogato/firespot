<script lang="js">
    import Map from 'ol/Map.js';
    import View from 'ol/View.js';
    import KML from 'ol/format/KML.js';
    import HeatmapLayer from 'ol/layer/Heatmap.js';
    import TileLayer from 'ol/layer/Tile.js';
    import StadiaMaps from 'ol/source/StadiaMaps.js';
    import VectorSource from 'ol/source/Vector.js';
    import {fromLonLat} from 'ol/proj.js';
    import {onMount} from 'svelte';

    let mapId = 20; 
    let map = null;

    const setupMap = (node) => {
        const source = new VectorSource();

        const vector = new HeatmapLayer({
            source: source,
            blur: 25,
            radius: 20,
            /*
            weight: function(feature) {
                const desc = feature.get('description');
                return parseFloat(desc) || 0;
            }*/
            weight: () => 1
        });

        const raster = new TileLayer({
            source: new StadiaMaps({
              layer: 'osm_bright',
            })
        })


        map = new Map({
            target: node,
            layers: [
                raster,
                vector
            ],
            view: new View({
                projection: 'EPSG:3857',
                center: fromLonLat([0, 0]),
                zoom: 2,
            })
        });



        fetch('https://firespot-backend.vercel.app/get-map')
            .then(r => r.text())
            .then(kmlData => {
                const format = new KML();
                const features = format.readFeatures(kmlData, {
                    dataProjection: 'EPSG:4326',
                    featureProjection: 'EPSG:4326' // keep in lon/lat for flipping later
                });


                // KML vs OpenLayers lon/lat order convention fix
                features.forEach(feature => {
                    const geom = feature.getGeometry();
                    if(geom.getType() == 'Point') {
                        const coords = geom.getCoordinates();
                        geom.setCoordinates([coords[1], coords[0]]);
                    }
                })
                features.forEach(f => {
                    f.getGeometry().transform('EPSG:4326', 'EPSG:3857');
                })

                source.addFeatures(features);

                    /*map.getView().fit(source.getExtent(), {
                        padding: [50,50,50,50]
                    });*/

                
            })
        


        return {
            destroy() {
                if (map) {
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
            height: 100%;
            margin: 0;
            top: 0;
            left: 0;
        }
  </style>


