document.addEventListener('DOMContentLoaded', function() {
    const showBtn = document.getElementById('show-btn');
    const spreadsheetSelect = document.getElementById('spreadsheet-select');
    const tableContainer = document.getElementById('table-container');
    const saveBtn = document.getElementById('save-btn'); // Nuevo botón de guardar
    let data; // Variable global para almacenar los datos de la hoja de cálculo

    showBtn.addEventListener('click', function() {
        const spreadsheetId = spreadsheetSelect.value;
        if (spreadsheetId) {
            fetchSpreadsheetData(spreadsheetId);
        } else {
            alert('Por favor, seleccione una hoja de cálculo.');
        }
    });

    // Agrega un listener al botón de guardar
    saveBtn.addEventListener('click', function() {
        const spreadsheetId = spreadsheetSelect.value;
        if (spreadsheetId) {
            saveChanges(spreadsheetId); // Llama a la función para guardar los cambios
        } else {
            alert('Por favor, seleccione una hoja de cálculo.');
        }
    });

    function fetchSpreadsheetData(spreadsheetId) {
        const url = `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/A1:Z100?key=AIzaSyCH8cUZfYqWURMijfPvs04Y1-wZYjDsZc8`;

        fetch(url)
            .then(response => response.json())
            .then(_data => {
                data = _data; // Almacena los datos en la variable global
                generateDynamicTable(data, tableContainer);
            })
            .catch(error => console.error('Error al obtener los datos:', error));
    }

    function generateDynamicTable(data, container) {
        container.innerHTML = '';

        const table = document.createElement('table');

        data.values.forEach(rowData => {
            const row = document.createElement('tr');

            rowData.forEach(cellData => {
                const cell = document.createElement('td');
                cell.textContent = cellData;
                cell.setAttribute('contenteditable', 'true'); // Hacer la celda editable
                row.appendChild(cell);
            });

            table.appendChild(row);
        });

        // Escucha los cambios en la tabla
        table.addEventListener('input', function(event) {
            const target = event.target;
            const rowIndex = target.parentElement.rowIndex - 1;
            const cellIndex = target.cellIndex;
            const newValue = target.textContent;

            // Actualiza los datos en la variable global
            data.values[rowIndex][cellIndex] = newValue;
        });

        container.appendChild(table);
    }

    // Función para guardar los cambios en la hoja de cálculo
    function saveChanges(spreadsheetId) {
        const range = 'A1:Z100'; // Rango de celdas para actualizar
        const valueInputOption = 'USER_ENTERED'; // Opción para interpretar los datos de entrada

        fetch(`https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${range}?key=AIzaSyCH8cUZfYqWURMijfPvs04Y1-wZYjDsZc8`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                values: data.values,
                valueInputOption: valueInputOption // Mover valueInputOption al cuerpo de la solicitud
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al guardar los cambios en la hoja de cálculo.');
            }
            alert('Cambios guardados correctamente.');
        })
        .catch(error => console.error('Error al guardar los cambios:', error));
    }
});
