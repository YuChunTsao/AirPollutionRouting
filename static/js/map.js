let map;
let routes;
let Voyager = L.tileLayer.provider('CartoDB.Voyager');
let TonerLite = L.tileLayer.provider('Stamen.TonerLite');

let baseMaps = {
    "TonerLite": TonerLite,
    "Voyager": Voyager
};

let overlayMaps = {
    
};

let popup = L.popup();

let temp_popup_latlng;
let originLatlng;
let destinationLatlng;


function displayPopup(e) {
    //e.latlng.toString()
    temp_popup_latlng = e.latlng;
    popup
        .setLatLng(e.latlng)
        .setContent(`
            <button name='start_point' onclick='setStartMarker();'>設為起點</button>
            <br><br>
            <button name='end_point' onclick='setEndMarker();'>設為終點</button>
        `)
        .openOn(map);
}

let redIcon = new L.Icon({
    iconUrl: './static/images/marker-icon-2x-red.png',
    shadowUrl: './static/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [0, -41],
    shadowSize: [41, 41]
});

let blueIcon = new L.Icon({
    iconUrl: './static/images/marker-icon-2x-blue.png',
    shadowUrl: './static/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [0, -41],
    shadowSize: [41, 41]
});

let startMarker = L.marker(null, {
    title: 'start point',
    icon: redIcon,
    draggable: true
});

let endMarker = L.marker(null, {
    title: 'end point',
    icon: blueIcon,
    draggable: true
});

// startMarker.bindPopup(`
//     <button id="remove_start_btn" name='remove_marker'>remove marker</button>
// `)

// endMarker.bindPopup(`
//     <button id="remove_end_btn" name='remove_marker'>remove marker</button>
// `)


// startMarker.on('click', function (e) {
//     let remove_start_btn = document.getElementById('remove_start_btn');
//     remove_start_btn.addEventListener('click', function () {
//         removeMarker(startMarker);
//     })
// })

startMarker.on('drag', function (e) {
    // console.log(e.latlng);
    document.getElementById('origin-input').value = e.latlng.toString();
    originLatlng = { lat: e.latlng.lat, lng: e.latlng.lng };
})

// endMarker.on('click', function (e) {
//     let remove_end_btn = document.getElementById('remove_end_btn');
//     remove_end_btn.addEventListener('click', function () {
//         removeMarker(endMarker);
//     })
// })

endMarker.on('drag', function (e) {
    // console.log(e.latlng);
    document.getElementById('destination-input').value = e.latlng.toString();
    destinationLatlng = { lat: e.latlng.lat, lng: e.latlng.lng };
})



function removeMarker(marker) {
    console.log(marker);
    map.closePopup();
}

function setStartMarker() {
    startMarker
        .setLatLng(temp_popup_latlng)
        .addTo(map)

    map.closePopup(popup);
    document.getElementById('origin-input').value = temp_popup_latlng.toString();
    originLatlng = { lat: temp_popup_latlng.lat, lng: temp_popup_latlng.lng };
}

function setEndMarker() {
    endMarker
        .setLatLng(temp_popup_latlng)
        .addTo(map)

    map.closePopup(popup);
    document.getElementById('destination-input').value = temp_popup_latlng.toString();
    destinationLatlng = { lat: temp_popup_latlng.lat, lng: temp_popup_latlng.lng };
}

function initMap() {
    map = L.map('map', {
        center: [25.017525, 121.540426],
        zoom: 15,
        layers: [TonerLite, Voyager]
    });

    L.control.layers(baseMaps, overlayMaps).addTo(map);

    map.on('contextmenu', displayPopup);

    route_1 = L.geoJSON(null, { style: function(feature) {
        return { color: feature.properties.color};
    }
    });
    route_2 = L.geoJSON(null, { style: function(feature) {
        return { color: feature.properties.color};
    }
    });
    route_3 = L.geoJSON(null, { style: function(feature) {
        return { color: feature.properties.color};
    }
    });
    route_4 = L.geoJSON(null, { style: function(feature) {
        return { color: feature.properties.color};
    }
    });
    route_5 = L.geoJSON(null, { style: function(feature) {
        return { color: feature.properties.color};
    }
    });
}
function DirectionsHandler() {
    this.originLatlng = null;
    this.distinationLatlng = null;
    this.travelMode = 'foot-walking';

    let originInput = document.getElementById('origin-input');
    let destinationInput = document.getElementById('destination-input');
    let modeSelector = document.getElementById('mode-selector');
    let submit = document.getElementById('direction-submit');

    // 選擇交通模式
    this.setupClickListener('changemode-foot-walking', 'foot-walking');
    this.setupClickListener('changemode-cycling-regular', 'cycling-regular');
    this.setupClickListener('changemode-driving-car', 'driving-car');

    this.setupSubmit();
}

DirectionsHandler.prototype.setupClickListener = function (id, mode) {
    var radioButton = document.getElementById(id);
    var me = this;

    radioButton.addEventListener('click', function () {
        me.travelMode = mode;
        // me.route();
    });
};

DirectionsHandler.prototype.setupSubmit = function () {
    var submit = document.getElementById('direction-submit');
    var me = this;

    submit.addEventListener('click', function () {
        document.getElementById('loading-page').style.display = 'block';
        document.getElementById('route-table-tb').innerHTML = '';

        // console.log(originLatlng);
        // console.log(destinationLatlng);
        // console.log(me.travelMode);

        let url = 'http://192.168.0.4:5005/my_direction_api';
        let data = {
            origin: originLatlng,
            destination: destinationLatlng,
            travelMode: me.travelMode
        };

        fetch(url, {
            body: JSON.stringify(data),
            method: 'POST',
            cache: 'no-cache',
            credentials: 'same-origin',
            headers: {
                'user-agent': 'Mozilla/4.0 MDN Example',
                'content-type': 'application/json'
            }
        })
            .then((response) => {
                return response.json();
            })
            .then((myjson) => {
                routes = myjson.result;
                let routes_list = [route_1, route_2, route_3, route_4, route_5]

                for (let i = 0; i < routes.length; i++) {
                    route = JSON.parse(routes[i].data);
                    route_info = routes[i].route_info;
                    console.log(route_info);

                    // insert data to  html table
                    let tb = document.getElementById('route-table-tb');
                    let tr = document.createElement('tr');

                    tr.style.cssText = 'text-align: center; vertical-align: middle;';

                    let th = document.createElement('th');
                    th.innerHTML = i + 1;
                    let th_attr = document.createAttribute('scope');
                    th_attr.value = 'row';
                    th.setAttributeNode(th_attr);

                    let checkbox_td = document.createElement('td');
                    let layer_switcher = document.createElement('input');
                    layer_switcher.value = i;
                    layer_switcher.id = 'checkbox_route_' + (i + 1);
                    layer_switcher.type = 'checkbox';
                    layer_switcher.onclick = function () {
                        let status = this.checked;
                        let route = routes_list[this.value];
                        console.log(route);

                        // zoom to layer
                        
                        if (status) {
                            // console.log("open");
                            // console.log(route);
                            route.addTo(map);
                            zoomToLayer(map, route);
                        }
                        else {
                            // console.log("close");
                            // console.log(route);
                            map.removeLayer(route);
                        }
                    };

                    checkbox_td.appendChild(layer_switcher);

                    let total_distance_td = document.createElement('td');
                    total_distance_td.innerHTML = route_info.total_distance.toFixed(2);

                    let total_exposure_td = document.createElement('td');
                    total_exposure_td.innerHTML = route_info.total_exposure.toFixed(2);

                    let total_duration_td = document.createElement('td');
                    total_duration_td.innerHTML = route_info.total_duration.toFixed(2);

                    let avg_exposure_td = document.createElement('td');
                    let avg_exposure_value = route_info.average_exposure.toFixed(2);
                    avg_exposure_td.innerHTML = avg_exposure_value

                    th.style.cssText = setColor(avg_exposure_value);

                    tr.appendChild(th);
                    tr.appendChild(checkbox_td);
                    tr.appendChild(total_exposure_td);
                    tr.appendChild(avg_exposure_td);
                    tr.appendChild(total_distance_td);
                    tr.appendChild(total_duration_td);
                    tb.appendChild(tr);

                    routes_list[i].addData(route);
                }
                document.getElementById('loading-page').style.display = 'none';
                document.getElementById('request-result').click();
                document.getElementById('checkbox_route_1').click();
            })
    });
};


function setColor(value) {
    let color = '';
    if (value <= 15.4)
        color = '#00E800'
    if (value > 15.4 && value <= 35.4)
        color = '#FFFF00'
    if (value > 35.4 && value <= 54.4)
        color = '#FF7E00'
    if (value > 54.4 && value <= 150.4)
        color = '#FF0000'
    if (value > 150.4 && value <= 250.4)
        color = '#8F3F97'
    if (value > 250.4 && value <= 350.4)
        color = '#7E0023'
    if (value > 350.4 && value <= 500.4)
        color = '#7E0023'

    return 'background-color:' + color
}

function zoomToLayer(map, layer) {
    let bounds = L.latLngBounds();
    layer.getLayers().forEach(function(feature) {
        // console.log(feature.getBounds());
        bounds.extend(feature.getBounds());
    })

    map.invalidateSize();
    map.fitBounds(bounds);
}