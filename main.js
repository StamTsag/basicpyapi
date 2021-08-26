let wss = new WebSocket('wss://basicpyapi.herokuapp.com')

wss.onopen = function(e) {
    document.getElementById('resp').textContent = 'Connection established.'
}

wss.onmessage = function(e) {
    document.getElementById('uid').textContent = JSON.parse(e.data)['uid']
    document.getElementById('resp').textContent = e.data
}

function genUid() {
    wss.send(JSON.stringify({'event': 'authenticate'}))
}