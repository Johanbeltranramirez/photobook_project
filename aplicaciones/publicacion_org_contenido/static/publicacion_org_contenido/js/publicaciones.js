(function () {
  function unoPorId(id) { return document.getElementById(id); }

  var zona = document.querySelector('[data-zona-archivo]');
  if (zona) {
    var entrada = zona.querySelector('input[type=file]');
    var previa = zona.querySelector('.pc-zona-previa');
    var nombre = unoPorId('pc_nombre_archivo');
    var ancho = unoPorId('id_ancho');
    var alto = unoPorId('id_alto');
    var duracion = unoPorId('id_duracionSegundos');
    var actual = null;

    function limpiarMedidas() {
      if (ancho) ancho.value = '';
      if (alto) alto.value = '';
      if (duracion) duracion.value = '';
    }

    function mostrar(archivo) {
      if (actual) URL.revokeObjectURL(actual);
      previa.innerHTML = '';
      limpiarMedidas();
      if (!archivo) { zona.classList.remove('con_archivo'); if (nombre) nombre.textContent = ''; return; }
      actual = URL.createObjectURL(archivo);
      var esVideo = archivo.type.indexOf('video/') === 0;
      var elemento = document.createElement(esVideo ? 'video' : 'img');
      elemento.src = actual;
      if (esVideo) {
        elemento.muted = true;
        elemento.controls = false;
        elemento.preload = 'metadata';
        elemento.addEventListener('loadedmetadata', function () {
          if (ancho) ancho.value = elemento.videoWidth || '';
          if (alto) alto.value = elemento.videoHeight || '';
          if (duracion && isFinite(elemento.duration)) duracion.value = Math.max(1, Math.round(elemento.duration));
        });
      } else {
        elemento.alt = 'Vista previa';
        elemento.addEventListener('load', function () {
          if (ancho) ancho.value = elemento.naturalWidth || '';
          if (alto) alto.value = elemento.naturalHeight || '';
        });
      }
      previa.appendChild(elemento);
      zona.classList.add('con_archivo');
      if (nombre) nombre.textContent = archivo.name + ' · ' + (archivo.size / 1048576).toFixed(1) + ' MB';
    }

    entrada.addEventListener('change', function () { mostrar(entrada.files[0]); });
    ['dragenter', 'dragover'].forEach(function (tipo) {
      zona.addEventListener(tipo, function () { zona.classList.add('arrastrando'); });
    });
    ['dragleave', 'drop'].forEach(function (tipo) {
      zona.addEventListener(tipo, function () { zona.classList.remove('arrastrando'); });
    });
  }

  document.querySelectorAll('[data-contador]').forEach(function (campo) {
    var salida = unoPorId(campo.getAttribute('data-contador'));
    var limite = campo.getAttribute('maxlength');
    if (!salida) return;
    function pintar() { salida.textContent = campo.value.length + (limite ? ' / ' + limite : ''); }
    campo.addEventListener('input', pintar);
    pintar();
  });

  var etiquetas = unoPorId('id_etiquetas');
  var vistaEtiquetas = unoPorId('pc_vista_etiquetas');
  if (etiquetas && vistaEtiquetas) {
    function pintarEtiquetas() {
      vistaEtiquetas.innerHTML = '';
      etiquetas.value.split(',').forEach(function (texto) {
        texto = texto.trim().replace(/^#+/, '');
        if (!texto) return;
        var chip = document.createElement('span');
        chip.className = 'pc-etiqueta';
        chip.textContent = '#' + texto;
        vistaEtiquetas.appendChild(chip);
      });
    }
    etiquetas.addEventListener('input', pintarEtiquetas);
    pintarEtiquetas();
  }

  var puntuacion = document.querySelector('.pc-puntuacion input[type=range]');
  if (puntuacion) {
    var valor = puntuacion.parentNode.querySelector('output');
    function pintarPuntuacion() { valor.textContent = Math.round(parseFloat(puntuacion.value || 0) * 100) + '%'; }
    puntuacion.addEventListener('input', pintarPuntuacion);
    pintarPuntuacion();
  }

  var nombreColeccion = unoPorId('id_nombre');
  var previaColeccion = document.querySelector('[data-previa-coleccion]');
  if (nombreColeccion && previaColeccion) {
    var descripcionColeccion = unoPorId('id_descripcion');
    var titulo = previaColeccion.querySelector('[data-previa-nombre]');
    var texto = previaColeccion.querySelector('[data-previa-descripcion]');
    var iconoPrivacidad = previaColeccion.querySelector('[data-previa-privacidad]');
    function pintarColeccion() {
      titulo.textContent = nombreColeccion.value.trim() || 'Nombre de la colección';
      texto.textContent = (descripcionColeccion && descripcionColeccion.value.trim()) || 'Aquí aparecerá la descripción.';
      var privada = document.querySelector('input[name=privacidad]:checked');
      if (iconoPrivacidad && privada) iconoPrivacidad.textContent = privada.value === 'privada' ? 'Privada' : 'Pública';
    }
    nombreColeccion.addEventListener('input', pintarColeccion);
    if (descripcionColeccion) descripcionColeccion.addEventListener('input', pintarColeccion);
    document.querySelectorAll('input[name=privacidad]').forEach(function (radio) { radio.addEventListener('change', pintarColeccion); });
    pintarColeccion();
  }

  document.querySelectorAll('form[data-confirmar]').forEach(function (formulario) {
    formulario.addEventListener('submit', function (evento) {
      if (!window.confirm(formulario.getAttribute('data-confirmar'))) evento.preventDefault();
    });
  });
})();
