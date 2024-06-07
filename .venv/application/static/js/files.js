document.addEventListener('DOMContentLoaded', function() {
    const showBtn = document.getElementById('show-btn');
    const spreadsheetSelect = document.getElementById('spreadsheet-select');
    const tableContainer = document.getElementById('table-container');
    const saveBtn = document.getElementById('save-btn');
    const generateChartBtn = document.getElementById('generate-chart-btn');
    const columnSelect = document.getElementById('column-select');
    const hideColumnBtn = document.getElementById('hide-column-btn');
    const showAllColumnsBtn = document.getElementById('show-all-columns-btn');
    const controlsContainer = document.getElementById('controls-container');
    const showFilesBtn = document.getElementById('show-files-btn');
    const folderSelect = document.getElementById('folder-select');
    const reportContainer = document.getElementById('report-container');
    const filterColumnSelect = document.getElementById('filter-column-select');
    const resultColumnSelect = document.getElementById('result-column-select');
    const generateReportBtn = document.getElementById('generate-report-btn');
    const filterValueInput = document.getElementById('filter-value');
    const reportResult = document.getElementById('report-result');

    showBtn.addEventListener('click', function() {
        const spreadsheetId = spreadsheetSelect.value;
        if (spreadsheetId) {
            fetchSpreadsheetData(spreadsheetId);
        } else {
            alert('Por favor, seleccione una hoja de cálculo.');
        }
    });

    showFilesBtn.addEventListener('click', function() {
        const folderId = folderSelect.value;
        fetchFiles(folderId);
    });

    saveBtn.addEventListener('click', function() {
        const spreadsheetId = spreadsheetSelect.value;
        if (spreadsheetId) {
            saveChanges(spreadsheetId);
        } else {
            alert('Por favor, seleccione una hoja de cálculo.');
        }
    });

    generateChartBtn.addEventListener('click', function() {
        const table = tableContainer.querySelector('table');
        if (!table) {
            alert('Primero debes mostrar los datos antes de generar un gráfico.');
            return;
        }
        const rows = table.querySelectorAll('tr');
        const labels = [];
        const data = [];

        rows.forEach((row, index) => {
            if (index !== 0) {
                const cells = row.querySelectorAll('td');
                labels.push(cells[0].textContent);
                const value = parseFloat(cells[1].textContent);
                if (!isNaN(value)) {
                    data.push(value);
                }
            }
        });

        if (labels.length > 0 && data.length > 0) {
            generateChart(labels, data);
        } else {
            alert('No hay suficientes datos numéricos para generar el gráfico.');
        }
    });

    function fetchFiles(folderId) {
        fetch('/get-files-from-folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'folder_id': folderId,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                spreadsheetSelect.innerHTML = '';
                data.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file.id;
                    option.textContent = file.name;
                    spreadsheetSelect.appendChild(option);
                });
            } else {
                alert('Error al obtener las hojas de cálculo.');
            }
        })
        .catch(error => console.error('Error fetching files:', error));
    }

    function fetchSpreadsheetData(spreadsheetId) {
        fetch('/show-spreadsheet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'spreadsheet_id': spreadsheetId,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                generateDynamicTable(data.data, tableContainer);
                generateColumnOptions(data.data[0]);
                showControls();
                showReportControls();
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error fetching spreadsheet data:', error));
    }

    function generateDynamicTable(data, container) {
        container.innerHTML = '';
        const table = document.createElement('table');
        const headerRow = document.createElement('tr');
        data[0].forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);
        data.slice(1).forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });
        container.appendChild(table);
    }

    function generateColumnOptions(headers) {
        columnSelect.innerHTML = '';
        filterColumnSelect.innerHTML = '';
        resultColumnSelect.innerHTML = '';

        headers.forEach(header => {
            const option1 = document.createElement('option');
            const option2 = document.createElement('option');
            const option3 = document.createElement('option');
            option1.value = header;
            option1.textContent = header;
            option2.value = header;
            option2.textContent = header;
            option3.value = header;
            option3.textContent = header;
            columnSelect.appendChild(option1);
            filterColumnSelect.appendChild(option2);
            resultColumnSelect.appendChild(option3);
        });
    }

    function showControls() {
        controlsContainer.classList.remove('hidden');
    }

    function showReportControls() {
        reportContainer.classList.remove('hidden');
    }

    hideColumnBtn.addEventListener('click', function() {
        const column = columnSelect.value;
        if (column) {
            hideColumn(column);
        }
    });

    showAllColumnsBtn.addEventListener('click', function() {
        showAllColumns();
    });

    function hideColumn(columnName) {
        const table = tableContainer.querySelector('table');
        if (!table) return;
        const headers = table.querySelectorAll('th');
        let columnIndex = -1;
        headers.forEach((header, index) => {
            if (header.textContent === columnName) {
                columnIndex = index;
            }
        });
        if (columnIndex === -1) return;
        headers[columnIndex].style.display = 'none';
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            row.children[columnIndex].style.display = 'none';
        });
    }

    function showAllColumns() {
        const table = tableContainer.querySelector('table');
        if (!table) return;
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.style.display = '';
        });
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            Array.from(row.children).forEach(cell => {
                cell.style.display = '';
            });
        });
    }

    generateReportBtn.addEventListener('click', function() {
        generateReport();
    });

    function generateReport() {
        const filterColumn = filterColumnSelect.value;
        const filterValue = filterValueInput.value;
        const resultColumns = Array.from(resultColumnSelect.selectedOptions).map(option => option.value);

        if (!filterColumn || !filterValue || resultColumns.length === 0 || resultColumns.length > 3) {
            alert('Por favor, seleccione la columna de filtro, ingrese un valor de filtro y seleccione hasta 3 columnas de resultado.');
            return;
        }

        const table = tableContainer.querySelector('table');
        if (!table) {
            alert('Primero debes mostrar los datos antes de generar un informe.');
            return;
        }

        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
        const filterColumnIndex = headers.indexOf(filterColumn);
        const resultColumnIndices = resultColumns.map(col => headers.indexOf(col));

        if (filterColumnIndex === -1 || resultColumnIndices.includes(-1)) {
            alert('Columnas de filtro o resultado no encontradas.');
            return;
        }

        const rows = table.querySelectorAll('tr');
        let result = 'No se encontró ningún valor que coincida.';
        const results = [];

        rows.forEach((row, rowIndex) => {
            if (rowIndex !== 0) {
                const cells = row.querySelectorAll('td');
                const cellValue = cells[filterColumnIndex]?.textContent;
                if (cellValue === filterValue) {
                    const resultValues = resultColumnIndices.map(index => cells[index]?.textContent || 'Resultado no encontrado');
                    results.push(resultValues.join(', '));
                }
            }
        });

        reportResult.textContent = results.length ? results.join('; ') : result;
    }

    function saveChanges(spreadsheetId) {
        const table = tableContainer.querySelector('table');
        if (!table) {
            alert('Primero debes mostrar los datos antes de guardarlos.');
            return;
        }
        const data = [];
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            const rowData = [];
            row.querySelectorAll('td').forEach(cell => {
                rowData.push(cell.textContent);
            });
            data.push(rowData);
        });

        fetch('/save-changes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                spreadsheet_id: spreadsheetId,
                data: data,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Los cambios se han guardado exitosamente.');
            } else {
                alert('Error al guardar los cambios.');
            }
        })
        .catch(error => console.error('Error saving changes:', error));
    }

    function generateChart(labels, data) {
        const chartContainer = document.createElement('div');
        chartContainer.classList.add('chart-container');
        const canvas = document.createElement('canvas');
        chartContainer.appendChild(canvas);
        document.body.appendChild(chartContainer);
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valores',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
});
