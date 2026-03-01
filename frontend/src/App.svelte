<script lang="js">
    import "ol/ol.css";

    import Map from "ol/Map.js";
    import View from "ol/View.js";
    import KML from "ol/format/KML.js";
    import HeatmapLayer from "ol/layer/Heatmap.js";
    import TileLayer from "ol/layer/Tile.js";
    import StadiaMaps from "ol/source/StadiaMaps.js";
    import VectorSource from "ol/source/Vector.js";
    import { fromLonLat } from "ol/proj.js";
    import { SimpleGeometry } from "ol/geom";

    //debug
    import VectorLayer from "ol/layer/Vector.js";
    import { Style, Circle, Fill } from "ol/style.js";

    // if there's a place u gotta go, im the one you needta know, im the map, im the map im the map
    let mapId = 20;
    let map = null;

    // bro what are the coords to nether fortress
    let lat = $state(null);
    let lon = $state(null);
    let coordLat = 0.0;
    let coordLon = 0.0;
    // let backend = http://129.212.186.70
    let backend = "https://team3-2.solarflare-godzilla.ts.net";

    let source = new VectorSource();

    let vector = new HeatmapLayer({
        source: source,
        blur: 60,
        radius: 50,
        weight: (f) => {
            const val = parseFloat(f.get("description")) || 0;
            return val * 5; // amplify
        },
    });

    const setupMap = (node) => {
        console.log("hey vro");
        // const source = new VectorSource();

        const raster = new TileLayer({
            source: new StadiaMaps({
                layer: "osm_bright",
            }),
        });

        map = new Map({
            target: node,
            layers: [raster, vector],
            view: new View({
                projection: "EPSG:3857",
                center: fromLonLat([0, 0]),
                zoom: 2,
            }),
        });

        return {
            destroy() {
                if (map) {
                    map.setTarget(null);
                    map = null;
                }
            },
        };
    };

    const updateMap = (node) => {
        console.log("yesss vro");
        console.log(lat);
        console.log(lon);

        if (lat != null) coordLat = lat;
        if (lon != null) coordLon = lon;

        map.getView().animate({
            zoom: 9.5,
            center: fromLonLat([coordLon, coordLat]),
            duration: 750,
        });

        fetch(`${backend}/get-map?latitude=${coordLat}&longitude=${coordLon}`)
            .then((r) => r.text())
            .then((kmlData) => {
                const format = new KML();
                const features = format.readFeatures(kmlData, {
                    dataProjection: "EPSG:4326",
                    featureProjection: "EPSG:4326", // keep in lon/lat for flipping later
                });

                console.log("features:", features.length);
                console.log(source);
                console.log(map.getLayers().getLength());

                // KML vs OpenLayers: lon/lat order convention
                features.forEach((feature) => {
                    const geom = feature.getGeometry();
                    if (geom instanceof SimpleGeometry) {
                        if (geom.getType() == "Point") {
                            const coords = geom.getCoordinates();
                            geom.setCoordinates([coords[1], coords[0]]);
                        }
                    }
                });
                features.forEach((f) => {
                    f.getGeometry().transform("EPSG:4326", "EPSG:3857");
                });

                source.clear();
                source.addFeatures(features);

                // map.getView().fit(source.getExtent(), {
                //    padding: [50,50,50,50]
                //});
            });

        return {
            destroy() {
                if (map) {
                    map.setTarget(null);
                    map = null;
                }
            },
        };
    };

    const checkLat = () => {};
    const checkLon = () => {};

    let address = $state("");

    const searchAddress = () => {
        if (!address.trim()) return;
        fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`,
            { headers: { "Accept-Language": "en" } },
        )
            .then((r) => r.json())
            .then((results) => {
                if (results.length === 0) {
                    alert("Address not found");
                    return;
                }
                lat = parseFloat(results[0].lat);
                lon = parseFloat(results[0].lon);
                updateMap();
            })
            .catch((err) => console.error("Geocoding error:", err));
    };
    
    const autofillLocation = () => {
      // ask for user's location
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(success, error);
      }
      
      function success(position) {
        console.log(position);
        lat = position.coords.latitude;
        lon = position.coords.longitude;
        updateMap();
      }
      function error() {
        alert("Could not get location!");
      }
    }
</script>

<link rel="stylesheet" href="node_modules/ol/ol.css" />
<div id={mapId} class="map" use:setupMap></div>

<div class="controls">
    <input
        bind:value={address}
        onkeydown={(e) => {
            if (e.key === "Enter") searchAddress();
        }}
        class="address-input"
        placeholder="Search address..."
    />
    <button class="enter" onclick={searchAddress}>Search</button>
    
    <div class="divider"></div>

    <input
        bind:value={lat}
        oninput={checkLat}
        onkeydown={(e) => {
            if (e.key === "Enter") updateMap();
        }}
        id="latIn"
        class="coord-input"
        placeholder="latitude"
    />

    <input
        bind:value={lon}
        oninput={checkLon}
        onkeydown={(e) => {
            if (e.key === "Enter") updateMap();
        }}
        id="lonIn"
        class="coord-input"
        placeholder="longitude"
    />

    <button id="enterbtn" class="enter" onclick={updateMap}>Enter</button>
    
    <div class="divider"></div>
    
    <button class="enter" onclick={autofillLocation}>Autofill</button>
    
</div>

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
    .address-input {
        font-size: 13px;
        padding: 4px 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
        width: 220px;
    }
    .divider {
        width: 1px;
        height: 20px;
        background: #ccc;
        margin: 0 4px;
    }
    .controls {
        position: absolute;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 8px;
        z-index: 2;
        background: rgba(255, 255, 255, 0.85);
        padding: 8px 12px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .coord-input {
        font-size: 13px;
        padding: 4px 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
        width: 130px;
    }
    .enter {
        font-size: 13px;
        padding: 4px 12px;
        border-radius: 4px;
        cursor: pointer;
    }
</style>
