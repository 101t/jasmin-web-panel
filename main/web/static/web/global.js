(function($){
    $(document).on("input", ".float-input", function(){this.value = this.value.replace(/[^0-9.]/g, ''); this.value = this.value.replace(/(\..*)\./g, '$1');});
    $(document).on("input", ".integer-input", function(){$(this).val($(this).val().replace(/[^0-9]/g, ''));});
    toastr.options.positionClass = 'toast-bottom-right';
    window.toTitleCase = function(str){
        return str.replace(/\w\S*/g, function(txt) {
			return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
		});
    }
    window.compare = function(a, b){
        if (a.order < b.order) {return -1;}
        if (a.order > b.order) {return 1;}
        return 0;
    }
    window.extend = function(obj, src){
        for(var key in src){
            if (src.hasOwnProperty(key)) obj[key] = src[key];
        }
        return obj;
    }
    window.delay = function(callback, ms){
        var timer = 0;
        return function() {
            var context = this, args = arguments;
    		clearTimeout(timer);
    		timer = setTimeout(function () {
      			callback.apply(context, args);
    		}, ms || 0);
        };
    }
    window.htmlEscape = function(str){
        return str
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }
    window.showThisBox = function(variant_boxes, box){
        variant_boxes = variant_boxes || [];
        var restOfBoxes = variant_boxes.filter(function(item, index, arr){return item !== box});
        $.each(restOfBoxes, function(k, v){$(v).hide()});
        $(box).show();
    }
    try {
        var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    } catch {}
    window.collection_check = function(tbody_html, page_no, destroy_paginate){
        tbody_html = tbody_html || function(val, i){return `<td>${val}</td>`;};
        page_no = page_no || 1;
        destroy_paginate = destroy_paginate || false;
        var per_page = parseInt($("#per_page").val());
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",

                page: page_no,
                per_page: per_page,
            },
            dataType: "json",
            success: function(data){
                var all_rows 	= data["length"];
				var datalist 	= data["data"];
                var pgnt_id 	= "#pagenumbers";
                if (!$(pgnt_id+" li").length || destroy_paginate) {
					var count = 1;
					var pagenumbers = '';
					if (datalist.length < all_rows) {
						pagenumbers += '<li class="page-item pg_prev"><a href="javascript:void(0)" class="page-link"><span>&laquo;</span></a></li>';
						for (var i = 0; i < all_rows; i += per_page) {
							pagenumbers += '<li class="page-item numeric'+(count === page_no?' page-current':'')+'">'+
								'<a href="javascript:void(0)" class="page-link">'+count+'</a>'+
							'</li>';
							count++;
						}
						pagenumbers += '<li class="page-item pg_next"><a href="javascript:void(0)" class="page-link"><span>&raquo;</span></a></li>';
						$(pgnt_id).html(pagenumbers);
						$(pgnt_id).closest("div").show();
						$(pgnt_id+" li.pg_prev, "+pgnt_id+" li.pg_next").on("click", function(){
							var length 	= $(pgnt_id+" li").length;
							var current = $(pgnt_id+" li.page-current");
							var index 	= current.index();
							var selector = $(this);
							if (selector.hasClass("pg_next")) {
								if (index < (length - 2)) {
									current.next("li").addClass("page-current");
									current.removeClass("page-current");
									collection_check(index + 1, false);
								}
							} else if (selector.hasClass("pg_prev")) {
								if (index > 1) {
									current.prev("li").addClass("page-current");
									current.removeClass("page-current");
									collection_check(index - 1, false);
								}
							}
						});
						$(pgnt_id+ " li.numeric").on("click", function(){
							var count = $(this).text();
							$(pgnt_id+' li').removeClass("page-current");
							$(this).addClass("page-current");
							collection_check(count, false);
						});
					} else {
						$(pgnt_id).html('');
						$(pgnt_id).closest("div").hide();
					}
                }
                var output = $.map(datalist, function(val, i){
                    var html = "";
                    html += `<tr>${tbody_html(val, i)}</tr>`;
                    return html;
                });
                $("#collectionlist").html(datalist.length > 0 ? output : $(".isEmpty").html());
            }
        })
    }
    window.collection_check_nopaginate = function(tbody_html) {
        tbody_html = tbody_html || function(val, i){return `<td>${val}</td>`;};
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",

                page: page_no,
                per_page: per_page,
            },
            dataType: "json",
            success: function(data){
                var datalist = data;
                var output = $.map(datalist, function(val, i){
                    var html = "";
                    html += `<tr>${tbody_html(val, i)}</tr>`;
                    return html;
                });
                $("#collectionlist").html(datalist.length > 0 ? output : $(".isEmpty").html());
            }
        })
    }
    window.quick_display_modal_error = function(html_response) {
        var html_message = `
            <p> An error occurred,<br/>
                <button type="button" class="btn btn-sm btn-danger float-right" class="show" data-toggle="modal"  data-target="#quick_display_modal" data-html="true">Show Error</button>
            <p>
        `;
        toastr.error(html_message, {closeButton: true, progressBar: true, enableHtml: true,});
        var html_source = html_response;
        html_source = html_source.replace(/["]/g, '&quot;')
        $("#quick_display_modal").closest('div').find('.modal-body').html('<iframe sandbox="allow-same-origin" srcdoc="'+html_source+'" class="iframe_error"></iframe>');
        if($("#collectionlist").length){
            $("#collectionlist").html($(".isEmpty").html());
        }
    }
    $("form").validate({
        errorClass: "text-danger",
        errorElementClass: 'text-success',
        errorElement: "small",
        rules: {
            cid: {
                required: true,
                rangelength: [2, 40],
            },
            gid: {
                required: true,
                maxlength: 40,
            },
            fid: {
                required: true,
                rangelength: [2, 40],
            },
            host: {
                required: true,
                rangelength: [7, 50],
            },
            port: {
                required: true,
                digits: true,
                rangelength: [2, 5],
            },
            order: {
                required: true,
                digits: true,
                rangelength: [1, 5],
            },
            rate: {
                required: true,
                number: true,
                maxlength: 10,
            },
            email: {
                required: true,
                email: true,
                minlength: 10,
            },
            username: {
                required: true,
                rangelength: [2, 50],
            },
            password: {
                required: true,
                rangelength: [2, 50],
            },
            password1: {
                required: true,
                rangelength: [2, 50],
            },
            password2: {
                required: true,
                rangelength: [2, 50],
                equalTo: "input[name=password1]",
            },
            url: {
                required: true,
                rangelength: [7, 250],
            }
        }
    });
})(jQuery);