function saveProfessors(escola_id) {
    const form = document.getElementById(`form_${escola_id}`);
    const formData = new FormData(form);

    fetch('/save_professors', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Informações salvas com sucesso!');
        } else {
            alert('Erro ao salvar informações.');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });

    return false;
}
