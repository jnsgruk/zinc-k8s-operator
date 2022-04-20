// This script is intended to be used with [k6](https://k6.io/)
// If you don't have zinc mapped to your localhost, you can pass
// the application IP, or ingress IP, using the environment 
// variable `ZINC_IP`.


import http from 'k6/http';
import { check } from 'k6';

export const options = {
    scenarios: {
        rampUp: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 20 },
                { duration: '1m', target: 20 },
                { duration: '30s', target: 100 },
                { duration: '1m', target: 100 },
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '0s'
        },
    }
}

export default function() {
    const res = http.get(`http://${__ENV.ZINC_IP || 'localhost'}:4080/ui/`);
    check(res, {
        'is status 200': (r) => r.status === 200,
    })
}