const net = require('node:net');

const input = {
    "method": "floor",
    "params": [23.3],
    "param_types": ["int"],
    "id": 1
}

const server_address = '/tmp/socket_file';
// サーバーへの接続
try {
    const client = net.createConnection({path: server_address}, () => {
        console.log(`connecting to ${server_address}`);
        const json_input = JSON.stringify(input);
        client.write(json_input)
    });
    client.on('data', (data) => {
        console.log(data.toString());
        client.end();
    });
    client.on('end', () => {
        console.log('disconnected from server');
    });
} catch {
    console.log("socket connection was not established")
}
