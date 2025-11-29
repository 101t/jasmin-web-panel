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
    
    // Toastr configuration
    if (typeof toastr !== 'undefined') {
        toastr.options.positionClass = 'toast-bottom-right';
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
    
    window.htmlEscape = function(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    };
    
    window.showThisBox = function(variant_boxes, box) {
        variant_boxes = variant_boxes || [];
        variant_boxes.filter(function(item) { return item !== box; })
            .forEach(function(v) { $(v).hide(); });
        $(box).show();
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
        tbody_html = tbody_html || function(val) { return '<td>' + val + '</td>'; };
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
                if (xhr.responseText) {
                    window.quick_display_modal_error(xhr.responseText);
                }
            }
        });
    };
    
    /**
     * Collection listing without pagination
     */
    window.collection_check_nopaginate = function(tbody_html) {
        tbody_html = tbody_html || function(val) { return '<td>' + val + '</td>'; };
        
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
            }
        });
    };
    
    /**
     * Display error in modal
     */
    window.quick_display_modal_error = function(html_response) {
        var html_message = '<p>An error occurred<br/>' +
            '<button type="button" class="btn btn-sm btn-danger float-right" data-toggle="modal" data-target="#quick_display_modal">Show Error</button></p>';
        
        if (typeof toastr !== 'undefined') {
            toastr.error(html_message, {closeButton: true, progressBar: true, enableHtml: true});
        }
        
        var html_source = (html_response || '').replace(/["]/g, '&quot;');
        $("#quick_display_modal .modal-body").html(
            '<iframe sandbox="allow-same-origin" srcdoc="' + html_source + '" class="iframe_error"></iframe>'
        );
        
        if ($("#collectionlist").length) {
            $("#collectionlist").html($(".isEmpty").html());
        }
    };
    
    // Form validation (if jQuery validate is available)
    if ($.fn.validate) {
        $("form").validate({
            errorClass: "text-danger",
            errorElement: "small",
            rules: {
                cid: { required: true, rangelength: [2, 40] },
                gid: { required: true, maxlength: 40 },
                fid: { required: true, rangelength: [2, 40] },
                host: { required: true, rangelength: [7, 50] },
                port: { required: true, digits: true, rangelength: [2, 5] },
                order: { required: true, digits: true, rangelength: [1, 5] },
                rate: { required: true, number: true, maxlength: 10 },
                email: { required: true, email: true, minlength: 10 },
                username: { required: true, rangelength: [2, 50] },
                password: { required: true, rangelength: [2, 50] },
                password1: { required: true, rangelength: [2, 50] },
                password2: { required: true, rangelength: [2, 50], equalTo: "input[name=password1]" },
                url: { required: true, rangelength: [7, 250] }
            }
        });
    }
})(jQuery);