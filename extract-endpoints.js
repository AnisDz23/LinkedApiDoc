const fs = require('fs');
const path = require('path');
const http = require('http');

const CONTROLLERS_DIR = '/home/linked/.openclaw/workspaces/linked-dev/linked-api/API/ComService.Controllers';
const API_ENDPOINT = 'http://localhost:3000/api/endpoints';
const AUTH = 'admin:admin';

// Read all .cs files
const controllerFiles = fs.readdirSync(CONTROLLERS_DIR).filter(f => f.endsWith('.cs'));

console.log(`Found ${controllerFiles.length} controller files`);

function extractControllerName(filename) {
    return filename.replace('Controller.cs', '');
}

function parseControllerFile(filepath) {
    const content = fs.readFileSync(filepath, 'utf8');
    const filename = path.basename(filepath);
    const controllerName = extractControllerName(filename);
    
    const endpoints = [];
    
    // HTTP methods mapping
    const httpMethods = {
        'HttpGet': 'GET',
        'HttpPost': 'POST',
        'HttpPut': 'PUT',
        'HttpDelete': 'DELETE',
        'HttpPatch': 'PATCH'
    };
    
    // Find all lines with Route attribute
    const lines = content.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check for HTTP method attribute
        let httpVerb = null;
        for (const [attr, verb] of Object.entries(httpMethods)) {
            if (line.includes(`[${attr}]`)) {
                httpVerb = verb;
                break;
            }
        }
        
        if (!httpVerb) continue;
        
        // Look for Route on next lines
        let route = null;
        for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
            const nextLine = lines[j].trim();
            if (nextLine.includes('[Route(')) {
                const match = nextLine.match(/\[Route\("([^"]+)"\)\]/);
                if (match) {
                    route = match[1];
                }
                break;
            }
            // Skip if we hit a non-attribute line
            if (nextLine && !nextLine.startsWith('[') && !nextLine.includes('Route')) {
                break;
            }
        }
        
        if (!route) continue;
        
        // Replace {controller} with actual controller name
        let finalRoute = route.replace('{controller}', controllerName);
        
        // Look for method signature to extract parameters
        let methodLine = '';
        let params = {};
        
        for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
            if (lines[j].includes('public') && (lines[j].includes('ActionResult') || lines[j].includes('public'))) {
                methodLine = lines[j];
                
                // Extract parameters
                const paramMatch = methodLine.match(/\(([^)]+)\)/);
                if (paramMatch) {
                    const paramsStr = paramMatch[1];
                    const paramParts = paramsStr.split(',');
                    
                    for (const paramPart of paramParts) {
                        const trimmed = paramPart.trim();
                        // Extract type and name
                        const paramTypeMatch = trimmed.match(/(\w+)\s+(\w+)(?:\s*\[)?/);
                        if (paramTypeMatch) {
                            const paramType = paramTypeMatch[1];
                            const paramName = paramTypeMatch[2];
                            
                            // Check for FromBody, FromQuery attributes
                            let paramLocation = 'string';
                            if (trimmed.includes('[FromBody]')) {
                                paramLocation = 'body';
                            } else if (trimmed.includes('[FromQuery]')) {
                                paramLocation = 'query';
                            }
                            
                            // Detect array types
                            if (paramType.toLowerCase().includes('list') || 
                                paramType.toLowerCase().includes('array') ||
                                paramType.toLowerCase().includes('ienumerable')) {
                                params[paramName] = 'array';
                            } else {
                                params[paramName] = paramType.toLowerCase();
                            }
                        }
                    }
                }
                break;
            }
        }
        
        endpoints.push({
            http_method: httpVerb,
            route: finalRoute,
            parameters: JSON.stringify(params),
            controller: controllerName,
            description: ''
        });
    }
    
    return endpoints;
}

// Check existing endpoints to avoid duplicates
function getExistingEndpoints() {
    return new Promise((resolve, reject) => {
        const auth = Buffer.from(AUTH).toString('base64');
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: '/api/endpoints',
            method: 'GET',
            headers: {
                'Authorization': `Basic ${auth}`,
                'Content-Type': 'application/json'
            }
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve([]);
                }
            });
        });
        
        req.on('error', reject);
        req.end();
    });
}

// Post endpoint to API
function postEndpoint(endpoint) {
    return new Promise((resolve, reject) => {
        const auth = Buffer.from(AUTH).toString('base64');
        const data = JSON.stringify(endpoint);
        
        const options = {
            hostname: 'localhost',
            port: 3000,
            path: '/api/endpoints',
            method: 'POST',
            headers: {
                'Authorization': `Basic ${auth}`,
                'Content-Type': 'application/json',
                'Content-Length': data.length
            }
        };
        
        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                if (res.statusCode === 201) {
                    resolve({ success: true, data: JSON.parse(body) });
                } else {
                    resolve({ success: false, error: body, endpoint });
                }
            });
        });
        
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    console.log('Fetching existing endpoints...');
    const existingEndpoints = await getExistingEndpoints();
    
    // Create a set of existing routes+methods to check for duplicates
    const existingSet = new Set(
        existingEndpoints.map(e => `${e.http_method}:${e.route}:${e.controller}`)
    );
    
    console.log(`Found ${existingEndpoints.length} existing endpoints`);
    
    let totalExtracted = 0;
    let totalInserted = 0;
    let errors = [];
    const controllerSummary = {};
    
    for (const file of controllerFiles) {
        const filepath = path.join(CONTROLLERS_DIR, file);
        const endpoints = parseControllerFile(filepath);
        const controllerName = extractControllerName(file);
        
        if (endpoints.length > 0) {
            controllerSummary[controllerName] = endpoints.length;
            totalExtracted += endpoints.length;
            
            console.log(`\n${controllerName}: ${endpoints.length} endpoints`);
            
            for (const endpoint of endpoints) {
                const key = `${endpoint.http_method}:${endpoint.route}:${endpoint.controller}`;
                
                if (existingSet.has(key)) {
                    console.log(`  SKIP (exists): ${endpoint.http_method} ${endpoint.route}`);
                    continue;
                }
                
                const result = await postEndpoint(endpoint);
                if (result.success) {
                    totalInserted++;
                    console.log(`  OK: ${endpoint.http_method} ${endpoint.route}`);
                } else {
                    errors.push({ endpoint, error: result.error });
                    console.log(`  ERROR: ${endpoint.http_method} ${endpoint.route} - ${result.error}`);
                }
            }
        }
    }
    
    console.log('\n\n========== SUMMARY ==========');
    console.log(`Total controllers processed: ${Object.keys(controllerSummary).length}`);
    console.log(`Total endpoints extracted: ${totalExtracted}`);
    console.log(`Total endpoints inserted: ${totalInserted}`);
    console.log(`Errors: ${errors.length}`);
    
    if (errors.length > 0) {
        console.log('\nErrors:');
        errors.forEach((e, i) => {
            console.log(`${i + 1}. ${e.endpoint.http_method} ${e.endpoint.route} - ${e.error}`);
        });
    }
    
    console.log('\nController Summary:');
    Object.entries(controllerSummary)
        .sort((a, b) => b[1] - a[1])
        .forEach(([controller, count]) => {
            console.log(`  ${controller}: ${count}`);
        });
}

main().catch(console.error);
