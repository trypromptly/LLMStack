(function() {
  var _initializedCache = [];

  function initJSONForm(element) {
    // Check if element has already been initialized
    if (_initializedCache.indexOf(element) !== -1) {
      return;
    }

    var dataInput = element;
    var dataInputId = element.id;

    var config = JSON.parse(element.dataset.djangoJsonform);
    config.data = JSON.parse(config.data);

    var containerId = element.id + '_jsonform';

    var container = element.previousElementSibling;
    container.setAttribute('id', element.id + '_jsonform');

    config.containerId = containerId;
    config.dataInputId = dataInputId;

    var jsonForm = reactJsonForm.createForm(config);

    if (config.validateOnSubmit) {
      var form = dataInput.form;
      form.addEventListener('submit', function(e) {
        var errorlist = container.parentElement.previousElementSibling;
        var hasError;

        if (errorlist && errorlist.classList.contains('errorlist'))
          hasError = true;
        else
          hasError = false;

        var validation = jsonForm.validate();

        if (!validation.isValid) {
          e.preventDefault();

          if (!hasError) {
            errorlist = document.createElement('ul');
            errorlist.setAttribute('class', 'errorlist');
            var errorli = document.createElement('li');
            errorli.textContent = 'Please correct the errors below.';
            errorlist.appendChild(errorli);

            container.parentElement.parentElement.insertBefore(
              errorlist, container.parentElement
            );
          }

          errorlist.scrollIntoView();
        } else {
          if (hasError)
            errorlist.remove();
        }
        jsonForm.update({ errorMap: validation.errorMap });
      });
    }
    jsonForm.render();
    _initializedCache.push(element);
  }

  /**
   * Helper function to determine if the element is being dragged, so that we
   * don't initialize the json form fields. They will get initialized when the dragging stops.
   *
   * @param element The element to check
   * @returns {boolean}
   */
  function isDraggingElement(element) {
    return 'classList' in element && element.classList.contains('ui-sortable-helper');
  }

  function initializeAllForNode(parentElement) {
    if (parentElement.querySelectorAll === undefined)
      return;

    var containers = parentElement.querySelectorAll('[data-django-jsonform]');

    // hacky way to filter NodeList using Array.filter
    [].filter.call(containers, function(container) {

      // filter out elements that contain '__prefix__' in their id
      // these are used by django formsets for template forms
      if (container.id.indexOf('__prefix__') > -1)
        return false;

      // filter out elements that contain '-empty-' in their ids
      // these are used by django-nested-admin for nested template formsets
      // also ensure that 'empty' is not actually the related_name for some relation
      // by checking that it is not surrounded by numbers on both sides
      if (container.id.match(/-empty-/) && !container.id.match(/-\d+-empty-\d+-/))
        return false;

      return true;
    })
    .forEach(initJSONForm);
  }

  function init() {
    // Initialize all json form fields already on the page.
    initializeAllForNode(document);

    // Setup listeners to initialize all json form fields as they get added to the page.
    if ('MutationObserver' in window) {
      new MutationObserver(function(mutations) {
        var mutationRecord;
        var addedNode;

        for (var i = 0; i < mutations.length; i++) {
          mutationRecord = mutations[i];

          if (mutationRecord.addedNodes.length > 0) {
            for (var j = 0; j < mutationRecord.addedNodes.length; j++) {

              addedNode = mutationRecord.addedNodes[j];

              if (isDraggingElement(addedNode))
                return;

              initializeAllForNode(addedNode);
            }
          }
        }
      }).observe(document.documentElement, { childList: true, subtree: true });
    } else {
      document.addEventListener('DOMNodeInserted', function(e) {
        if (isDraggingElement(e.target))
          return;

        initializeAllForNode(e.target);
      });
    }
  }

  if (document.readyState === 'interactive' ||
      document.readyState === 'complete' ||
      document.readyState === 'loaded') {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', function() {
      init();
    });
  }

})();
