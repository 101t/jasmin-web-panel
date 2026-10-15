/**
 * Global utilities and configurations for Jasmin Web Panel
 */
(function($) {
    'use strict';

    // Input masks
    $(document).on("input", ".float-input", function() {
        this.value = this.value.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');
    });
    $(document).on("input", ".integer-input", function() {
        $(this).val($(this).val().replace(/[^0-9]/g, ''));
    });

    // Toastr configuration. Messages often quote jcli output, so never render them as HTML.
    if (typeof toastr !== 'undefined') {
        toastr.options.positionClass = 'toast-bottom-right';
        toastr.options.closeButton = true;
        toastr.options.progressBar = true;
        toastr.options.escapeHtml = true;
    }

    // Utility functions
    window.toTitleCase = function(str) {
        return str.replace(/\w\S*/g, function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    };

    window.compare = function(a, b) {
        return (a.order < b.order) ? -1 : (a.order > b.order) ? 1 : 0;
    };

    window.extend = function(obj, src) {
        for (var key in src) {
            if (src.hasOwnProperty(key)) obj[key] = src[key];
        }
        return obj;
    };

    window.delay = function(callback, ms) {
        var timer = 0;
        return function() {
            var context = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function() {
                callback.apply(context, args);
            }, ms || 0);
        };
    };

    /** Escape any value (numbers and null included) for safe insertion into HTML. */
    window.escapeHtml = function(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    };
    window.htmlEscape = window.escapeHtml;

    /** A translated interface string from global_trans (set in web/base.html), or the English fallback. */
    var trans = window.trans = function(key, fallback) {
        return (window.global_trans && global_trans[key]) || fallback;
    };

    /** Filter the rows of a table body by the text typed in a [data-table-filter] search box. */
    window.applyTableFilter = function(input) {
        var $input = $(input), term = $.trim($input.val()).toLowerCase();
        var $tbody = $($input.data('table-filter'));
        $tbody.children('tr.filter-empty').remove();
        var rows = 0, shown = 0;
        $tbody.children('tr').each(function() {
            var $row = $(this);
            if ($row.children('td[colspan]').length) return;  // loading, empty or error row
            var match = !term || $row.text().toLowerCase().indexOf(term) !== -1;
            $row.toggle(match);
            rows++;
            if (match) shown++;
        });
        if (rows && !shown) {
            $('<tr class="filter-empty"><td colspan="100" class="text-center text-muted py-3"></td></tr>')
                .find('td').text(trans('noMatch', 'Nothing matches your search.')).end().appendTo($tbody);
        }
    };
    $(document).on('input', '[data-table-filter]', function() { window.applyTableFilter(this); });
    // Lists are reloaded over AJAX after every change: keep the current search applied.
    $(document).ajaxComplete(function() {
        $('[data-table-filter]').each(function() { window.applyTableFilter(this); });
    });

    window.showThisBox = function(variant_boxes, box) {
        variant_boxes = variant_boxes || [];
        variant_boxes.filter(function(item) { return item !== box; })
            .forEach(function(v) { $(v).hide(); });
        $(box).show();
    };

    /**
     * Turn a failed request into a message a person can act on. The panel answers with
     * {"message": ...} JSON; a proxy error page, a network failure or an expired session do not.
     */
    window.ajaxErrorMessage = function(jqXHR) {
        var data = jqXHR.responseJSON;
        if (!data) {
            try { data = JSON.parse(jqXHR.responseText); } catch (e) { data = null; }
        }
        if (data && data.message) return data.message;
        if (data && data.error) return data.error;
        if (jqXHR.status === 0) return trans('unreachable', 'The panel server cannot be reached, check your connection.');
        return trans('requestFailed', 'Request failed') + ' (' + jqXHR.status + ' ' + (jqXHR.statusText || 'error') + ').';
    };

    window.showAjaxError = function(jqXHR) {
        var data = jqXHR.responseJSON || {};
        if (jqXHR.status === 401) {
            // Session expired: send the user to the login page and back here afterwards.
            var login = data.login_url || '/account/login/';
            window.location.href = login + '?next=' + encodeURIComponent(window.location.pathname);
            return;
        }
        if (typeof toastr !== 'undefined') {
            toastr.error(window.ajaxErrorMessage(jqXHR));
        }
    };

    window.showAjaxSuccess = function(data) {
        if (typeof toastr !== 'undefined' && data && data.message) {
            toastr.success(data.message);
        }
    };

    /** Placeholder rows for a table body while it loads, or when loading failed. */
    window.tableLoading = function(tbody, colspan) {
        $(tbody).html('<tr><td colspan="' + (colspan || 1) + '" class="text-center text-muted py-4">' +
            '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span>' +
            trans('loading', 'Loading...') + '</td></tr>');
    };

    window.tableError = function(tbody, colspan, jqXHR, retry) {
        var $row = $('<tr><td class="text-center text-danger py-4"></td></tr>');
        $row.find('td').attr('colspan', colspan || 1)
            .append($('<i class="fas fa-exclamation-triangle mr-2"></i>'))
            .append(document.createTextNode(window.ajaxErrorMessage(jqXHR)));
        if (retry) {
            $('<button type="button" class="btn btn-sm btn-outline-secondary ml-3"></button>')
                .text(trans('retry', 'Retry'))
                .on('click', retry)
                .appendTo($row.find('td'));
        }
        $(tbody).empty().append($row);
        if (jqXHR.status === 401) window.showAjaxError(jqXHR);
    };

    /** Ask before a destructive action, then run onConfirm. */
    window.confirmAction = function(onConfirm, text) {
        sweetAlert({
            title: global_trans["areyousuretodelete"],
            text: text || global_trans["youwontabletorevertthis"],
            type: 'warning',
            showCancelButton: true,
            cancelButtonClass: "btn btn-secondary m-btn m-btn--pill m-btn--icon",
            cancelButtonText: global_trans["no"],
            confirmButtonClass: "btn btn-danger m-btn m-btn--pill m-btn--air m-btn--icon",
            confirmButtonText: global_trans["yes"],
        }, function(isConfirm) {
            if (isConfirm) onConfirm();
        });
    };

    /**
     * Submit a modal form over AJAX: validate, lock the form and show progress on the submit
     * button while the gateway works, then report the outcome.
     */
    window.submitAjaxForm = function(form, onSuccess) {
        var $form = $(form);
        if ($.fn.valid && $form.data('validator') && !$form.valid()) return;
        var data = $form.serialize(); // before disabling: disabled inputs are not serialized
        var $inputs = $form.find("input, select, button, textarea");
        var $submit = $form.find("button[type=submit]");
        var label = $submit.html();
        $.ajax({
            type: "POST",
            url: $form.attr("action"),
            data: data,
            beforeSend: function() {
                $inputs.prop("disabled", true);
                $submit.html('<span class="spinner-border spinner-border-sm mr-1" role="status" aria-hidden="true"></span>' + label);
            },
            success: function(response) {
                window.showAjaxSuccess(response);
                $form.closest(".modal").modal("hide");
                if (onSuccess) onSuccess(response);
            },
            error: window.showAjaxError,
            complete: function() {
                $inputs.prop("disabled", false);
                $submit.html(label);
            }
        });
    };

    /** POST a single command (delete, enable, ...) to a manage endpoint. */
    window.postAction = function(url, data, onSuccess) {
        return $.ajax({
            type: "POST",
            url: url,
            data: $.extend({csrfmiddlewaretoken: csrfmiddlewaretoken}, data),
            dataType: "json",
            success: function(response) {
                window.showAjaxSuccess(response);
                if (onSuccess) onSuccess(response);
            },
            error: window.showAjaxError
        });
    };

    // Get CSRF token and path
    var local_path = window.location.pathname;
    var csrfmiddlewaretoken = '';
    try {
        var csrfEl = document.getElementsByName('csrfmiddlewaretoken')[0];
        if (csrfEl) csrfmiddlewaretoken = csrfEl.value;
    } catch(e) {}

    /**
     * Collection listing with pagination
     */
    window.collection_check = function(tbody_html, page_no, destroy_paginate) {
        tbody_html = tbody_html || function(val) { return '<td>' + escapeHtml(val) + '</td>'; };
        page_no = page_no || 1;
        destroy_paginate = destroy_paginate || false;
        var per_page = parseInt($("#per_page").val()) || 10;

        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",
                page: page_no,
                per_page: per_page
            },
            dataType: "json",
            success: function(data) {
                var all_rows = data.length || 0;
                var datalist = data.data || [];
                var pgnt_id = "#pagenumbers";

                if (!$(pgnt_id + " li").length || destroy_paginate) {
                    var count = 1;
                    var pagenumbers = '';
                    if (datalist.length < all_rows) {
                        pagenumbers += '<li class="page-item pg_prev"><a href="javascript:void(0)" class="page-link"><span>&laquo;</span></a></li>';
                        for (var i = 0; i < all_rows; i += per_page) {
                            pagenumbers += '<li class="page-item numeric' + (count === page_no ? ' page-current' : '') + '">' +
                                '<a href="javascript:void(0)" class="page-link">' + count + '</a></li>';
                            count++;
                        }
                        pagenumbers += '<li class="page-item pg_next"><a href="javascript:void(0)" class="page-link"><span>&raquo;</span></a></li>';
                        $(pgnt_id).html(pagenumbers).closest("div").show();

                        // Pagination click handlers
                        $(pgnt_id + " li.pg_prev, " + pgnt_id + " li.pg_next").on("click", function() {
                            var current = $(pgnt_id + " li.page-current");
                            var index = current.index();
                            var length = $(pgnt_id + " li").length;

                            if ($(this).hasClass("pg_next") && index < (length - 2)) {
                                current.removeClass("page-current").next("li").addClass("page-current");
                                collection_check(tbody_html, index + 1, false);
                            } else if ($(this).hasClass("pg_prev") && index > 1) {
                                current.removeClass("page-current").prev("li").addClass("page-current");
                                collection_check(tbody_html, index - 1, false);
                            }
                        });

                        $(pgnt_id + " li.numeric").on("click", function() {
                            $(pgnt_id + ' li').removeClass("page-current");
                            $(this).addClass("page-current");
                            collection_check(tbody_html, parseInt($(this).text()), false);
                        });
                    } else {
                        $(pgnt_id).html('').closest("div").hide();
                    }
                }

                var output = datalist.map(function(val, i) {
                    return '<tr>' + tbody_html(val, i) + '</tr>';
                });
                $("#collectionlist").html(output.length > 0 ? output.join('') : $(".isEmpty").html());
            },
            error: function(xhr) {
                window.tableError("#collectionlist", $("#collectionlist").closest("table").find("thead th").length, xhr);
            }
        });
    };

    /**
     * Collection listing without pagination
     */
    window.collection_check_nopaginate = function(tbody_html) {
        tbody_html = tbody_html || function(val) { return '<td>' + escapeHtml(val) + '</td>'; };

        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list"
            },
            dataType: "json",
            success: function(data) {
                var datalist = Array.isArray(data) ? data : (data.data || []);
                var output = datalist.map(function(val, i) {
                    return '<tr>' + tbody_html(val, i) + '</tr>';
                });
                $("#collectionlist").html(output.length > 0 ? output.join('') : $(".isEmpty").html());
            },
            error: window.showAjaxError
        });
    };

    /**
     * Display error in modal
     */
    window.quick_display_modal_error = function(html_response) {
        if (typeof toastr !== 'undefined') {
            toastr.error(trans('errorDetails', 'An error occurred, see the details window.'));
        }

        var html_source = (html_response || '').replace(/["]/g, '&quot;');
        $("#quick_display_modal .modal-body").html(
            '<iframe sandbox="allow-same-origin" srcdoc="' + html_source + '" class="iframe_error"></iframe>'
        );
        $("#quick_display_modal").modal("show");

        if ($("#collectionlist").length) {
            $("#collectionlist").html($(".isEmpty").html());
        }
    };

    // Form validation for the gateway forms (those posting to a ".../manage/" endpoint).
    // The limits mirror what Jasmin itself accepts, so mistakes are caught before a round trip.
    if ($.fn.validate) {
        $.validator.addMethod('jasminId', function(value, element) {
            return this.optional(element) || /^[A-Za-z0-9_-]+$/.test(value);
        }, trans('jasminId', 'Only letters, digits, "_" and "-" are allowed.'));

        var jasminRules = {
            cid: { required: true, jasminId: true, rangelength: [3, 25] },
            gid: { required: true, jasminId: true, maxlength: 16 },
            uid: { required: true, jasminId: true, maxlength: 16 },
            fid: { required: true, jasminId: true, maxlength: 16 },
            username: { required: true, jasminId: true, maxlength: 15 },
            password: { maxlength: 16 },  // required where the input has the "required" attribute
            host: { required: true, maxlength: 255 },
            port: { required: true, digits: true, range: [1, 65535] },
            order: { required: true, digits: true },
            rate: { number: true, min: 0 },
            url: { required: true, url: true }
        };
        $('form[action$="/manage/"]').each(function() {
            var rules = $.extend(true, {}, jasminRules);
            if (/smppccm\/manage\/$/.test($(this).attr('action'))) {
                // SMPP connector credentials belong to the remote SMSC, not to a Jasmin user.
                rules.username = { required: true, maxlength: 16 };
                rules.password = {};
            }
            $(this).validate({
                errorClass: "text-danger",
                errorElement: "small",
                rules: rules,
                // Submission goes through submitAjaxForm, which checks $form.valid() first.
                submitHandler: function() {}
            });
        });
    }
})(jQuery);
