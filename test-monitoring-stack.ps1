# test-monitoring-stack.ps1

Write-Host "=== Testing Monitoring Stack ===" -ForegroundColor Cyan

# 1. Check if containers are running
Write-Host "`n[1] Checking container status..." -ForegroundColor Green
docker ps --filter "name=prometheus|elasticsearch|kibana|metricbeat" --format "table {{.Names}}\t{{.Status}}"

# 2. Check Prometheus is scraping
Write-Host "`n[2] Checking Prometheus targets..." -ForegroundColor Green
$promTargets = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -UseBasicParsing | ConvertFrom-Json
Write-Host "Active targets: $($promTargets.data.activeTargets.count)"
$promTargets.data.activeTargets | ForEach-Object { Write-Host "  - $($_.labels.job)" }

# 3. Check Elasticsearch connectivity
Write-Host "`n[3] Checking Elasticsearch health..." -ForegroundColor Green
$esHealth = Invoke-WebRequest -Uri "http://localhost:9200/_cluster/health" -UseBasicParsing | ConvertFrom-Json
Write-Host "Status: $($esHealth.status)"
Write-Host "Nodes: $($esHealth.number_of_nodes)"

# 4. Check if metricbeat indices exist
Write-Host "`n[4] Checking Metricbeat indices in Elasticsearch..." -ForegroundColor Green
$indices = Invoke-WebRequest -Uri "http://localhost:9200/_cat/indices?format=json" -UseBasicParsing | ConvertFrom-Json
$metricbeatIndices = $indices | Where-Object { $_.index -like "metricbeat-*" }
if ($metricbeatIndices.count -gt 0) {
    Write-Host "✓ Found $($metricbeatIndices.count) metricbeat index(es)"
    $metricbeatIndices | ForEach-Object { Write-Host "  - $($_.index) ($($_.docs.count) docs)" }
} else {
    Write-Host "⚠ No metricbeat indices found yet (may take 10-20 seconds after startup)"
}

# 5. Check Metricbeat logs for errors
Write-Host "`n[5] Checking Metricbeat container logs (last 20 lines)..." -ForegroundColor Green
docker logs --tail 20 metricbeat

# 6. Query Metricbeat data from Elasticsearch
Write-Host "`n[6] Querying prometheus metrics from Elasticsearch..." -ForegroundColor Green
$query = @{
    query = @{
        match = @{
            "metricset.module" = "prometheus"
        }
    }
    size = 5
} | ConvertTo-Json

$esQuery = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_search" `
    -Method POST `
    -ContentType "application/json" `
    -Body $query `
    -UseBasicParsing | ConvertFrom-Json

if ($esQuery.hits.total.value -gt 0) {
    Write-Host "✓ Found $($esQuery.hits.total.value) prometheus metric documents"
    Write-Host "`nSample document:"
    $esQuery.hits.hits[0]._source | ConvertTo-Json | Write-Host
} else {
    Write-Host "⚠ No prometheus metrics found yet"
}

# 7. Kibana endpoint check
Write-Host "`n[7] Checking Kibana accessibility..." -ForegroundColor Green
$kibanaHealth = Invoke-WebRequest -Uri "http://localhost:5601/api/status" -UseBasicParsing -ErrorAction SilentlyContinue
if ($kibanaHealth.StatusCode -eq 200) {
    Write-Host "✓ Kibana is accessible at http://localhost:5601"
} else {
    Write-Host "⚠ Kibana returned status: $($kibanaHealth.StatusCode)"
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "If all checks pass, open Kibana: http://localhost:5601" -ForegroundColor Yellow