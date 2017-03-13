var RATTIC = (function ($, ZeroClipboard) {
  var my = {
    api: {},
    controls: {},
    page: {}
  },
  /********* Private Variables *********/
    credCache = [],
    rattic_meta_prefix = 'rattic_',
    pass_settings = {
      lcasealpha: {
        description: "Lowercase Alphabet",
        candefault: true,
        mustdefault: false,
        set: "abcdefghijklmnopqrstuvwxyz"
      },
      ucasealpha: {
        description: "Upper Alphabet",
        candefault: true,
        mustdefault: false,
        set: "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      },
      numbers: {
        description: "Numbers",
        candefault: true,
        mustdefault: false,
        set: "0123456789"
      },
      special: {
        description: "Special",
        candefault: false,
        mustdefault: false,
        set: "!@#$%^&*()_-+=:;\"',.<>?/\|"
      },
      spaces: {
        description: "Spaces",
        candefault: false,
        mustdefault: false,
        set: " "
      }
    };

  /********* Page Methods **********/
  /* Get Meta information */
  my.page.getMetaInfo = function (name) {
    return $('head meta[name=' + rattic_meta_prefix + name + ']').attr('content');
  };

  /* Gets the cred for the page from the head */
  my.page.getCredId = function () {
    return my.page.getMetaInfo('cred_id');
  };

  /* Gets the the url root from the page */
  my.page.getURLRoot = function () {
    return my.page.getMetaInfo('url_root');
  };

  /* Gets the the url root from the page */
  my.page.getStaticURL = function (file) {
    return my.page.getMetaInfo('url_root') + 'static/' + file;
  };

  /* Setup ZeroClipboard */
  ZeroClipboard.config({ moviePath: my.page.getStaticURL('zeroclipboard/1.3.2/ZeroClipboard.swf') });

  /********* Private Methods **********/
  /* Gets a cookie from the browser. Only works for cookies that
   * are not set to httponly */
  function _getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) == (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /* Shortcut to get the CSRF cookie from django. Tastypie needs this to
   * perform session based authentication. */
  function _getCsrf() {
    return _getCookie('csrftoken');
  }

  /* Build an API URL */
  function _apiurl(object, method, data, options) {
    var url,
      qsbits,
      qsbit;
    /* Build the base URL */
    if (method == 'GET' && typeof data != 'undefined') {
      url = my.page.getURLRoot() + 'api/v1/' + object + '/' + data + '/';
    } else {
      url = my.page.getURLRoot() + 'api/v1/' + object + '/';
    }

    /* Build the query string */
    if (typeof options != 'undefined') {
      qsbits = [];
      for (var key in options) {
        qsbit = [key, options[key]].join('=');
        qsbits.push(qsbit);
      }
      url += '?' + qsbits.join('&');
    }

    return url;
  }

  /* Generic API call to Rattic. Handles the CSRF token and callbacks */
  function _apicall(object, method, data, success, failure, options) {
    var url = _apiurl(object, method, data, options);

    if (method == 'GET') data = undefined;

    return $.ajax({
      url: url,
      type: method,
      contentType: 'application/json',
      beforeSend: function (jqXHR, settings) {
        jqXHR.setRequestHeader('X-CSRFToken', _getCsrf())
      },
      data: data,
      success: success,
      failure: failure
    });
  }

  function _apicallwait(object, method, data, options) {
    var url = _apiurl(object, method, data, options);

    if (method == 'GET') {
      data = undefined;
    }

    return $.parseJSON($.ajax({
      url: url,
      type: method,
      contentType: 'application/json',
      beforeSend: function (jqXHR, settings) {
        jqXHR.setRequestHeader('X-CSRFToken', _getCsrf());
      },
      data: data,
      async: false
    }).responseText);
  }

  /* When the password button is clicked */
  function _passShowButtonClick() {
    var target = $($(this).data('target'));
    switch ($(this).data('status')) {
    case 'hidden':
      _passShowButtonShow($(this), target);
      break;
    case 'shown':
      _passShowButtonHide($(this), target);
      break;
    }
    return false;
  }

  /* If we are going to show the password */
  function _passShowButtonShow(button, target) {
    //target.trigger('getdata');
    button.trigger('show');
    button.data('status', 'shown');
    button.html('<i class="icon-eye-close"></i>');
    target.removeClass('passhidden');
    if (target.prop('tagName') == 'INPUT') {
      target.attr('type', 'text');
    }
  }

  /* If we were asked to hide the password */
  function _passShowButtonHide(button, target) {
    button.trigger('hide');
    button.data('status', 'hidden');
    button.html('<i class="icon-eye-open"></i>');
    target.addClass('passhidden');
    if (target.prop('tagName') == 'INPUT') {
      target.attr('type', 'password');
    }
  }

  function _performCredSearch() {
    var searchstr = $(this).children('input[type=search]').val();
    var app = window.location.pathname.split("/")[1];

    if (searchstr.length > 0) {
      if (app == "request") {
        window.location = my.page.getURLRoot() + "request/list-by-search/" + searchstr + "/";
      } else {
        window.location = my.page.getURLRoot() + "cred/list-by-search/" + searchstr + "/";
      }
    }

    return false;
  }

  function _checkAllClick() {
    var me = $(this),
      targets = $(me.data('target')),
      mystatus = me.is(':checked');

    targets.each(function () {
      me = $(this);
      if (me.prop('checked') != mystatus) {
        me.trigger('click');
      }
    });
  }

  function _countChecks(checkboxes) {
    return checkboxes.filter(':checked').length;
  }

  function _disablebuttons(button) {
    if (button.hasClass('btn')) {
      button.addClass('disabled');
    } else if (button.hasClass('selectized')) {
      button[0].selectize.disable();
    } else {
      button.hide();
    }
  }

  function _enablebuttons(button) {
    if (button.hasClass('btn')) {
      button.removeClass('disabled');
    } else if (button.hasClass('selectized')) {
      button[0].selectize.enable();
    } else {
      button.show();
    }
  }

  function _enableButtonHandler() {
    $.each($(this).data('linked'), function () {
      var button = $(this),
        target = $(button.data('target'));
      if (_countChecks(target) > 0) {
        _enablebuttons(button);
      } else {
        _disablebuttons(button);
      }
    });
  }

  function _newTagClick() {
    var me = $(this),
      input = $($(this).data('input')),
      inputval = input.val(),
      message = $($(this).data('message')),
      ajax = RATTIC.api.createTag(
        inputval,
        function () {
          if (ajax.status == 201) {
            input.val('');
            if (me.data('dismiss') == 'modal') {
              document.location.reload();
            } else {
              message.text(inputval + ' has been created.');
            }
          }
        },
        function () {}
      );
  }

  function _setVisibility(item, state) {
    if (state == true) {
      state = 'visible';
    }
    if (state == false) {
      state = 'hidden';
    }
    $(item).css({visibility: state});
  }

  function _hideCopyButton() {
    var me = $(this),
      button = $($(me).data('copybutton')),
      hideTimeoutId = window.setTimeout(_hideCopyButtonTimer.bind(undefined, button), 250);
    button.data('hideTimeoutId', hideTimeoutId);
  }

  function _hideCopyButtonTimer(button) {
    _setVisibility(button, false);
    button.data('hideTimeoutId', -1);
  }

  function _showCopyButton() {
    var button = $($(this).data('copybutton')),
      target = $(button.data('copyfrom')),
      hideTimeoutId = button.data('hideTimeoutId'),
      clip = button.data('clip');

    if (typeof button.data('hideTimeoutId') === "undefined") {
      button.data('hideTimeoutId', -1);
    }

    if (hideTimeoutId != -1) {
      window.clearTimeout(hideTimeoutId);
      button.data('hideTimeoutId', -1);
    }

    target.trigger('getdatasync');
    _setVisibility(button, true);
  }

  function _copyButtonGetData(client) {
    var me = $(this),
      target = $(me.data('copyfrom'));

    target.trigger('getdatasync');
    client.setText(target.text());
  }

  function _passfetcher() {
    var me = $(this),
      cred_id = me.data('cred_id');

    my.api.getCred(cred_id, function (data) {
        me.text(data['password']);
      },
      function () {});
  }

  function _passfetchersync() {
    var me = $(this),
      cred_id = me.data('cred_id');
    me.text(my.api.getCredWait(cred_id)['password']);
  }

  function _parentFormSubmit() {
    var me,
      form;
    if (this.hasOwnProperty('$input')) {
      me = this.$input;
    } else {
      me = $(this);
      if (me.hasClass('disabled')) {
        return false;
      }
    }

    form = me.parents('form:first');
    form.attr('action', me.data('action'));
    form.submit();
  }

  function _makePassword(length, can, must) {
    var pass = "",
      canset = "",
      x;

    // get chars we must have
    for (x = 0; x < must.length; x++) {
      pass += _randomString(1, pass_settings[must[x]]['set']);
    }

    // get chars we can have
    for (x = 0; x < can.length; x++) {
      canset += pass_settings[can[x]]['set'];
    }

    // Make the rest of the password with 'can' chars
    pass += _randomString(length - pass.length, canset);

    // Shuffle the password
    pass = pass.split("");
    for (x = 0; x < pass.length; x++) {
      var num = x + Math.abs(sjcl.random.randomWords(1)[0] % (pass.length - x));
      var tmp = pass[num];
      pass[num] = pass[x];
      pass[x] = tmp;
    }

    return pass.join("");
  }

  function _randomString(length, sourcechars) {
    if (sourcechars.length == 0) {
      return "";
    }

    var charcount = sourcechars.length;
    var strout = "";

    for (var x = 0; x < length; x++) {
      var charnum = Math.abs(sjcl.random.randomWords(1)[0]) % charcount;
      strout += sourcechars[charnum];
    }

    return strout;
  }

  function _genPassClick() {
    var me = $(this),
      input = $(me.data('input')),
      canset = [],
      mustset = [],
      passlength = parseInt($("#txt_length").val(), 10);

    for (var key in pass_settings) {
      if ($('#chk_must_' + key).is(":checked")) mustset.push(key);
      if ($('#chk_can_' + key).is(":checked")) canset.push(key);
    }

    if (passlength > 1000) {
        $("#txt_length").val(1000);
        passlength = 1000;
    }

    input.val(_makePassword(passlength, canset, mustset));
  }

  function _clickableIconClick() {
    var me = $(this),
      iconname = me.data('icon-name'),
      txtfield = $(me.data('txt-field')),
      imgfield = $(me.data('img-field')),
      newtag = imgfield.clone();

    txtfield.val(iconname);
    newtag.attr('class', me.attr('class'));
    newtag.removeClass('rattic-icon-clickable');
    imgfield.replaceWith(newtag);
  }

  function _newTagEntered(tagname, callback) {
    var successcall = _newTagSuccess.bind(undefined, callback);

    my.api.createTag(tagname, successcall, function () {});
  }

  function _newTagSuccess(callback, data, stext, ajax) {
    callback(data);
  }

  function _newGroupEntered(groupname, callback) {
    var successcall = _newGroupSuccess.bind(undefined, callback);

    my.api.createGroup(groupname, successcall, function () {});
  }

  function _newGroupSuccess(callback, data, stext, ajax) {
    callback(data);
  }

  function _singleTagLoad(query, callback) {
    my.api.searchTag(query,
      function (data) {
        callback(data['objects']);
      },
      function () {
        callback();
      }
    );
  }

  function _wrapInputAppend(input) {
    /* If we are not already wrapped */
    if (!$(input).parents('div').first().hasClass('input-append')) {
      /* Create a div and move everything inside */
      var div = $(document.createElement('div'));
      div.addClass('input-append');
      input.wrap(div);
    }
  }

  /********* Public Variables *********/

  /********* Public Methods *********/
  /* Creates a Group */
  my.api.createGroup = function (name, success, failure) {
    var data = JSON.stringify({
      'name': name
    });

    return _apicall('group', 'POST', data, success, failure);
  };

  /* Creates a Tag */
  my.api.createTag = function (name, success, failure) {
    var data = JSON.stringify({
      'name': name
    });

    return _apicall('tag', 'POST', data, success, failure);
  };

  /* Creates a Tag */
  my.api.searchTag = function (search, success, failure) {
    return _apicall('tag', 'GET', undefined, success, failure, {
      'name__contains': search
    });
  };

  /* Gets a cred */
  my.api.getCred = function (id, success, failure) {
    if (typeof credCache[id] == 'undefined') {
      _apicall('cred',
        'GET',
        id,
        function (data) {
          credCache[id] = data;
          success(data);
        },
        failure
      );
    } else {
      success(credCache[id]);
    }
  };

  /* Gets a cred synchronous version */
  my.api.getCredWait = function (id) {
    if (typeof credCache[id] == 'undefined') {
      credCache[id] = _apicallwait('cred', 'GET', id);
      return credCache[id];
    } else {
      return credCache[id];
    }
  };

  /* Adds a show/hide button to an input */
  my.controls.passInputShowHideButton = function (inputs) {
    inputs.each(function () {
      var me = $(this),
        button = $(document.createElement('button'));

      /* Make the button look attached */
      _wrapInputAppend(me);

      /* Create our button */

      button.addClass('btn btn-password-visibility');
      button.html('<i class="icon-eye-open"></i>');
      button.data('status', 'hidden');
      button.data('target', me);
      button.on('click', _passShowButtonClick);

      /* Add the button after the password input */
      me.after(button);
    });
  };

  /* Makes a button show or hide a span */
  my.controls.spanShowHideButton = function (inputs) {
    inputs.html('<i class="icon-eye-open"></i>');
    inputs.data('status', 'hidden');
    inputs.on('click', _passShowButtonClick);
  };

  /* Adds a show/hide button to an input */
  my.controls.addPasswordGenerator = function (inputs) {
    inputs.each(function () {
      var me = $(this),
        button = $(document.createElement('a'));

      /* Make the button look attached */
      _wrapInputAppend(me);

      /* Create our button */
      button.addClass('btn');
      button.html('<i class="icon-repeat"></i>');
      button.attr('data-toggle', 'modal');
      button.attr('id', 'genpass');
      button.attr('role', 'button');
      button.attr('href', '#passgenmodal');

      /* Add the button after the password input */
      me.after(button);
    });
  };

  /* Creates a password show and hide button */
  my.controls.searchForm = function (form) {
    form.on('submit', _performCredSearch);
  };

  /* Creates a checkbox that controls other checkboxes */
  my.controls.checkAll = function (checkboxes) {
    checkboxes.on('click', _checkAllClick);
  };

  /* A button that is enabled when at least one box is checked */
  my.controls.checkEnabledButton = function (buttons) {
    buttons.each(function () {
      var button = $(this),
        target = $($(this).data('target'));
      if (target.length == 0) return;
      if (typeof target.data('linked') == "undefined") {
        target.data('linked', []);
        target.on('click', _enableButtonHandler);
      }
      target.data('linked').push(button);
    });
  };

  /* Adds functionality for the 'New Tag' button */
  my.controls.newTagButton = function (tagbuttons) {
    tagbuttons.on('click', _newTagClick);
  };

  /* Add copy buttons to table cells */
  my.controls.tableCopyButtons = function (cells) {
    if (!FlashDetect.installed) {
      return false;
    }

    cells.each(function () {
      // Get the players
      var me = $(this),
        button = me.children('button'),
        text = me.children('span'),
        clip = new ZeroClipboard(button);

      // Set data for callbacks
      button.data('copyfrom', text);
      button.data('copybutton', button);
      button.data('clip', clip);
      me.data('copybutton', button);
      text.data('copybutton', button);

      // Apply callbacks
      me.on('mouseleave', _hideCopyButton);
      text.on('mouseover', _showCopyButton);
      clip.on('mouseover', _showCopyButton);
      clip.on('dataRequested', _copyButtonGetData);
    });

    return true;
  };

  /* Add data fetchers for the password spans */
  my.controls.passwordFetcher = function (fetcher, id) {
    fetcher.data('cred_id', id);
    //fetcher.on('getdata', _passfetcher);
    //fetcher.on('getdatasync', _passfetchersync);
  };

  /* Buttons that change a forms action, then submit it */
  my.controls.formSubmitButton = function (buttons) {
    buttons.on('click', _parentFormSubmit);
  };

  /* Add functionality to the password generator form */
  my.controls.genPasswordModal = function (form) {
    var button = $(form.data('button'));
    var input = $(form.data('input'));
    button.data('form', form);
    button.data('input', input);
    button.on('click', _genPassClick);
  };

  /* Add functionality to the password generator form */
  my.controls.clickableIcons = function (icons) {
    icons.on('click', _clickableIconClick);
  };

  /* Make the tag select boxes be awesome */
  my.controls.tagSelectors = function (selectors) {
    selectors.selectize({
      valueField: 'id',
      labelField: 'name',
      searchField: 'name',
      plugins: ['remove_button'],
      create: _newTagEntered
    });
  };

  /* Make the tag select boxes be awesome */
  my.controls.groupSelectors = function (selectors) {
    var options = {
      valueField: 'id',
      labelField: 'name',
      searchField: 'name',
      plugins: ['remove_button']
    };

    /* Staff members can create groups */
    if (my.page.getMetaInfo('user_staff') == 'true') {
      options.create = _newGroupEntered;
    }

    selectors.selectize(options);
  };

  /* Make the tag select boxes be awesome */
  my.controls.singleTagSelectors = function (selectors) {
    var s = selectors.selectize({
      valueField: 'id',
      labelField: 'name',
      searchField: 'name',
      preload: true,
      load: _singleTagLoad,
      create: _newTagEntered,
      onChange: _parentFormSubmit
    });

    if (s.length > 0) {
      s[0].selectize.disable();
    }
  };

  my.controls.formSubmitById = function (button) {
    button.on('click', function () {
      var me = $(this),
        target = $(me.data('form'));
      target.submit();
    });
  };
  return my;
}(jQuery, ZeroClipboard));

$(document).ready(function () {
  // Setup Icons
  $('.rattic-icon').css('background-image',
    'url(' + RATTIC.page.getStaticURL('rattic/img/sprite.png') + ')');

  // Search boxes
  RATTIC.controls.searchForm($('.rattic-cred-search'));

  // Password generator buttons
  RATTIC.controls.addPasswordGenerator($('input.btn-password-generator'));

  // Password Show/Hide buttons on password inputs
  RATTIC.controls.passInputShowHideButton($('input.btn-password-visibility'));

  // Password Show/Hide button on the details page
  RATTIC.controls.spanShowHideButton($('.btn-password-show-hide'));

  // Enable the password fetcher
  RATTIC.controls.passwordFetcher($('#password'), RATTIC.page.getCredId());

  // Setup checkboxes that check all values
  RATTIC.controls.checkAll($('input.rattic-checkall[type=checkbox]'));

  // Setup buttons that require one checked box to be enabled
  RATTIC.controls.checkEnabledButton($('.rattic-check-enabled'));

  // Add functionality to the 'New Tag' buttons
  RATTIC.controls.newTagButton($('.rattic-new-tag'));

  // Add copy buttons to table cells
  RATTIC.controls.tableCopyButtons($('td.rattic-copy-button'));

  // Buttons that have an action set and submit a form
  RATTIC.controls.formSubmitButton($('button.rattic-form-submit'));

  // Add functionality to the password generator form
  RATTIC.controls.genPasswordModal($('.rattic-password-generator'));

  // Add functionality to clickable icons
  RATTIC.controls.clickableIcons($('.rattic-icon-clickable'));

  // Tag selectors that can create tags
  RATTIC.controls.tagSelectors($('.rattic-tag-selector'));

  // A Group selector that will create for staff members
  RATTIC.controls.groupSelectors($('.rattic-group-selector'));

  // Button that submits a form indicated by a data attribute
  RATTIC.controls.formSubmitById($('.rattic-form-submit-by-id'));

  // Tags selectors that cannot create new tags
  $('.selectize-multiple').selectize({
    plugins: ['remove_button'],
    create: false
  });

  // Tag selectors for single tags
  RATTIC.controls.singleTagSelectors($('.rattic-single-tag-selector'));

  // Start collecting random numbers
  sjcl.random.startCollectors();
});

