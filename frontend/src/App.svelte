<script lang="js">
    import 'ol/ol.css';

    import Map from 'ol/Map.js';
    import View from 'ol/View.js';
    import KML from 'ol/format/KML.js';
    import HeatmapLayer from 'ol/layer/Heatmap.js';
    import TileLayer from 'ol/layer/Tile.js';
    import StadiaMaps from 'ol/source/StadiaMaps.js';
    import VectorSource from 'ol/source/Vector.js';
    import {fromLonLat} from 'ol/proj.js';
    import {onMount} from 'svelte';

    // if there's a place u gotta go, im the one you needta know, im the map, im the map im the map
    let mapId = 20; 
    let map = null;

    // bro what are the coords to nether fortress
    let lat = $state(0.0);
    lat = null;
    let lon = $state(0.0);
    lon = null;
    let coordLat = 0.0;
    let coordLon = 0.0;

    const setupMap = (node) => {
        console.log("hey vro");
        const source = new VectorSource();

        const vector = new HeatmapLayer({
            source: source,
            blur: 1,
            radius: 5,
            weight: function(feature) {
                const desc = feature.get('description');
                return parseFloat(desc) || 0;
            }
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

        return {
            destroy() {
                if (map) {
                    map.setTarget(null);
                    map = null;
                }
            }
        }
    }

    const updateMap = (node) => {
        console.log("yesss vro");
        console.log(lat);
        console.log(lon);

        if(lat != null) coordLat = lat;
        if(lon != null) coordLon = lon;

        map.getView().animate({center: fromLonLat([coordLon, coordLat])}, {duration: 1000});
        map.getView().animate({zoom: 13}, {duration: 750});  

        /*
        fetch('https://firespot-backend.vercel.app/get-map')
            .then(r => r.text())
            .then(kmlData => {
                const format = new KML();
                const features = format.readFeatures(kmlData, {
                    dataProjection: 'EPSG:4326',
                    featureProjection: 'EPSG:4326' // keep in lon/lat for flipping later
                });


                // KML vs OpenLayers: lon/lat order convention fix to lat/long
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

                    // map.getView().fit(source.getExtent(), {
                    //    padding: [50,50,50,50]
                    //}); 
            })
        */

        return {
            destroy() {
                if (map) {
                    map.setTarget(null);
                    map = null;
                }
            }
        }
    }

    const checkLat = () => {
        
    }
    const checkLon = () => {

    }

</script>


<link rel="stylesheet" href="node_modules/ol/ol.css">
<div id={mapId} class="map" use:setupMap></div>

<input bind:value={lat} oninput={checkLat} id=latIn class="lat" placeholder="latitude" />

<input bind:value={lon} oninput={checkLon} id=lonIn class="lon" placeholder="longitude">

<button id=enterbtn class="enter" onclick={updateMap}>
    Enter
</button>

<style>
    .map {
        overflow: hidden;
        position: absolute;
        width: 100vw;
        height: 100%;
        margin: 0;
        top: 0;
        left: 0;
        z-index: 1;
    }
    .lat {
        position: absolute;
        top: 95%;
        left: 10px;
        z-index: 1;
    }
    .lon {
        position: absolute;
        top: 95%;
        left: 165px;
        size: 15px;
        z-index: 1;
    }
    .enter {
        position: absolute;
        top: 95%;
        left: 325px;
        font-size: 12px;
        z-index: 2;
    }
</style>

