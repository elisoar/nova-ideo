//see: http://stackoverflow.com/questions/946534/insert-text-into-textarea-with-jquery/946556#946556
jQuery.fn.extend({
  insertAtCaret: function(myValue){
    return this.each(function(i) {
      if (document.selection) {
        //For browsers like Internet Explorer
        this.focus();
        sel = document.selection.createRange();
        sel.text = myValue;
        this.focus();
      }
      else if (this.selectionStart || this.selectionStart == '0') {
        //For browsers like Firefox and Webkit based
        var startPos = this.selectionStart;
        var endPos = this.selectionEnd;
        var scrollTop = this.scrollTop;
        this.value = this.value.substring(0, startPos)+myValue+this.value.substring(endPos,this.value.length);
        this.focus();
        this.selectionStart = startPos + myValue.length;
        this.selectionEnd = startPos + myValue.length;
        this.scrollTop = scrollTop;
      } else {
        this.value += myValue;
        this.focus();
      }
    })
  }
});

function loading_progress(){
    $('img.novaideo-loading-indicator').removeClass('hide-bloc');
}

function finish_progress(){
    $('img.novaideo-loading-indicator').addClass('hide-bloc');
}

function focus_on_form(container){
    setTimeout(function(){
     var form = $(container.find('form')).first()
     if (form.length > 0){
        deform.focusFirstInput(form);
     }
   }, 200)
}

var emoji = undefined

function get_new_emoji(){
    emoji = new EmojiConvertor();
    var emoji_url = $(document.body).data('emoji_url')
    emoji.img_sets = {
      'apple' : {'path' : emoji_url,
                 'sheet' : emoji_url,
                 'mask' : 1 }
    };
    emoji.use_sheet = true;
    emoji.init_env();
    return emoji
}


function init_emoji(nodes){
    // emojify.setConfig(
    //   {emojify_tag_type : 'span',
    //    img_dir          : 'http://0.0.0.0:6543/novaideostatic/emoji/image/sprites/'});
    // emojify.defaultConfig['mode'] = 'sprite'
    // emojify.run();

  if(emoji == undefined){
      emoji = get_new_emoji();
  }
  emoji.img_set = 'apple';
  emoji.text_mode = false;
  emoji.include_title = true;
  emoji.addAliases({
      '🤔' : '1f415'
  });
  for(var i=0; i< nodes.length; i++){
    var node = $(nodes[i])
    node.html(emoji.replace_colons(node.html()));
    node.addClass('emojified')
  }
}

function update_notification_id(id, url){
   $.post(url, {id: id}, function(data) {
     console.log(data)

   });
}

function send_vote(event){
  var $this = $(this)
  var panel = $($this.parents('.panel').first())
  var modal = $(panel.parents('.modal').first())
  var group = $($this.parents('.panel-group'))
  var button = $($this.find('button').first())
  var formData = new FormData($this[0]);
  formData.append(button.val(), button.val())
  var url = $this.attr('action')
  button.addClass('disabled');
  loading_progress()
  $.ajax({
      url: url,
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      success: function(data) {
        var has_error = $(data).find('.amendment-body .has-error').length > 0
        if(!has_error){
          var panel_to_remove = panel.find('.panel-collapse').first().attr('id')
          var source_body = $('<div>'+jQuery.parseJSON($('#'+modal.data('source')).data('body'))+'</div>')
          source_body.find('#'+panel_to_remove).parents('.panel').remove()
          panel.remove()
          $('#'+modal.data('source')).data('body', JSON.stringify(source_body.html()))
          var votes = $(group.find('.panel-title.collapsed'))
          if(votes.length>0){
            $(votes.first()).click()
            finish_progress()
          }else{
             modal.modal('hide')
             location.reload();
          }
        }else{
          button.removeClass('disabled');
          //TODO display errors
          finish_progress()
        }
       }
  });
  event.preventDefault();
}

function collapse_current_collpsein(){
  var current_btn = $(this);
  var btns = $('.navbar-toggle.collapsed');
  for(var i = 0; i<= btns.length; i++){
      var btn = $(btns[i]);
      if (btn != current_btn){
        $(btn.data('target')).collapse('hide');
      }
  }

}

function activate_explanation(event){
  if($(event.target).parents('.proposal-explanation').length == 0){
    var explanation = $($(this).find('.proposal-explanation').first());
    explanation.removeClass('hide-bloc');}
};

function close_explanation(event){
    var explanation = $($(this).parents('.proposal-explanation').first());
    explanation.addClass('hide-bloc');
};


function set_visited(){
    $.cookie('visited', 'true', {path: '/',  expires: 1});
}


function reset_cookie_channels_bar(){
  var $this = $('.all-channels');
  if ($this.hasClass('toggled')){
    $.cookie('channels', 'off', {path: '/',  expires: 1});
  }else{
     $.cookie('channels', 'on', {path: '/',  expires: 1});
  }
}

function init_channels_scroll(){
  if (!window.matchMedia("(max-width: 767px)").matches) {
    $('.channels-container').mCustomScrollbar({
        theme:"dark",
        scrollInertia: 100,
        scrollButtons:{
          enable: true
        },
        callbacks:{
        onScroll:function(){
            update_unread_messages_alerts()
        }}
      });
  }else{
    $('.channels-container').scroll(function(){
            update_unread_messages_alerts()
    })
  }
}

function init_channels_top(){
    var navbar_top_h = $('.navbar.navbar-fixed-top').height()
    navbar_top_h = navbar_top_h == undefined? 0 : navbar_top_h 
    var navbar_h = $('nav.navbar.navbar-bottom').height()
    navbar_h = navbar_h == undefined? 0 : navbar_h
    var default_top = navbar_h + navbar_top_h - 3
    var scrolltop = $(window).scrollTop();
    var btn = $('.all-channels-toggle:not(.close)')
    var blocks = $('.all-blocks')
    if (scrolltop <= navbar_h){
      btn.css('top', default_top - scrolltop+"px")
      blocks.css('margin-top', default_top - scrolltop+"px")
    }else{
      btn.css('top', default_top - navbar_h+"px")
      blocks.css('margin-top', default_top - navbar_h+"px")
    }
  }

function initscroll(){
  var result_scrolls = $(".result-scroll")
    for(var i = 0; i<= result_scrolls.length; i++){
      var result_scroll = $(result_scrolls[i]);
      var id = result_scroll.attr('id')
      var to_infinite = result_scroll
    if (!window.matchMedia("(max-width: 767px)").matches) {
      result_scroll.mCustomScrollbar({
      theme:"dark",
      scrollInertia: 100,
      scrollButtons:{
        enable: true
      },
      callbacks:{
        onTotalScroll:function(){
          $(this).trigger('scroll');
        }
      }
    });
      to_infinite = result_scroll.find('.mCSB_container')
    }
  $(to_infinite).infinitescroll({
    behavior: 'local',
    bufferPx: 0,

    binder: result_scroll,
    navSelector  : "#"+id+" .batch",
    // selector for the paged navigation (it will be hidden)
    nextSelector : "#"+id+" .pager .next",
    // selector for the NEXT link (to page 2)
    itemSelector : "#"+id+" .result-container",

    pathParse: function(path, next_page) {
       var id = result_scroll.attr('id')
       var filter = $('#filter-'+id);
       var sort = $('#sort-'+id);
       var data_get = ''
       if (filter.length>0){
            var form = $($(filter).find('form').first());
            var filter_container = $(form.parents('.filter-container'));
            var filter_btn = $(filter_container.find('.filter-btn').first());
            data_get = $(form).serialize();
            data_get += '&'+'op=filter_result';
            var filter_source = filter_btn.data('filter_source');
            if (filter_source !== ''){
              data_get += '&'+'filter_source='+filter_source;
            }
            data_get += '&'+'filter_result=true';
            data_get += '&'+'scroll=true';
            data_get += '&'+'view_only=1';
      };
       if (sort.length>0){
          var sort_form = $(sort.find('form').first()).serialize();
          data_get += '&'+sort_form;
       }

       var f = function(currPage) {
          var next_path = $($('#'+id+' .result-container').first().parents('div').first().find('>.result-container').last()).data('nex_url')
          return next_path +'&'+ data_get;
       };
       return f;
    },
    loading: {
      finishedMsg: '<span class="label label-warning">'+ novaideo_translate("No more item.")+"</span>",
      img: window.location.protocol + "//" + window.location.host + "/novaideostatic/images/progress_bar.gif",
      msgText: "",
    }
  },
  function(arrayOfNewElems){
    init_emoji($('.emoji-container:not(.emojified)'));
    var next = $($(this).find('.result-container').last()).data('nex_url')
    if(next){
      var currentbtn = $($(this).find('.btn-more-scroll').last())
     $($(this).find('.btn-more-scroll').not(currentbtn)).remove()
    }else{
     $($(this).find('.btn-more-scroll')).remove()
    }
  }); 
 }
};


function open_node_url(){
    window.open($($(this).parents('.node').first().find('.node-shape').first()).attr('url'))
}


$(document).on('dblclick', 'g.node .node-shape, g.node text', open_node_url)


$(document).on('click', '.btn-more-scroll', function(){
  var result_scroll = $($(this).parents('.result-scroll').first())
  result_scroll.mCustomScrollbar(
    'scrollTo','bottom', {
        scrollInertia: 1
    });
  result_scroll.scrollTop(result_scroll[0].scrollHeight);
})

function init_content_text(){
     var texts = $('.content-text');
     for(i=0; i<texts.length; i++){
         if ($(texts[i]).height()>600){
             $(texts[i]).addClass("content-text-scroll")
         }
     }
};

function init_result_scroll(event, default_top, element){
  if(default_top == undefined){
    default_top = 1600
  }
  var result_scrolls = element? $(element.find('.result-scroll')): $('.result-scroll');
  for(var i = 0; i<= result_scrolls.length; i++){
    var result_scroll = $(result_scrolls[i]);
    var items = $(result_scroll.find('.result-item, .small-result'));
    var last_child = items.last()
    if (last_child.length > 0){
        var top = last_child.offset().top - result_scroll.offset().top  + last_child.height()
        if(items.length < 8){
          top += 50
        }else{
          top -= 10
        }
        if (top < default_top){
         result_scroll.height(top);
        }else{
          result_scroll.height(default_top);
        }
    }else{
         result_scroll.height(100);
    }
 }
};

function init_morecontent_scroll(){
  var result_scrolls = $('.more-content-carousel');
  for(var i = 0; i<= result_scrolls.length; i++){
    var result_scroll = $(result_scrolls[i]);
    var last_child = $(result_scroll.find('.search-item').last());
    if (last_child.length > 0){
        var top = last_child.offset().top - result_scroll.offset().top  + last_child.height() + 150
        if (top < 1600){
         result_scroll.height(top);
        }
    }else{
         result_scroll.height(100);
    }
 }
};


function more_content(elements, isvertical){
    try{
      elements.slick({
        vertical: isvertical,
        centerMode: true,
        dots: false,
        slidesToShow: 5,
        slidesToScroll: 5,
        // autoplay: true,
        // autoplaySpeed: 8000,
        // infinite: true,
        responsive: [
            {
              breakpoint: 1024,
              settings: {
                slidesToShow: 5,
                slidesToScroll: 5,
                // infinite: true,
                dots: false
              }
            },
            {
              breakpoint: 600,
              settings: {
                slidesToShow: 2,
                slidesToScroll: 2
              }
            },
            {
              breakpoint: 480,
              settings: {
                slidesToShow: 1,
                slidesToScroll: 1
              }
            }
            // You can unslick at a given breakpoint now by adding:
            // settings: "unslick"
            // instead of a settings object
         ]
       });
  }
  catch(err) {
  }

}


function scroll_to_panel(){
  var url = document.location.toString();
  if ( url.match('#') ) {
      var panel = $('#'+url.split('#')[1])
      panel.addClass('in');
      panel.animate({scrollTop : 0},800);
  }
}

function rebuild_scrolls(scrolls){
  if (!window.matchMedia("(max-width: 767px)").matches) {
    if(scrolls == undefined){
      scrolls = $(".malihu-scroll")
    }
    if(scrolls.length>0){
      scrolls.mCustomScrollbar({
        theme:"minimal-dark",
        scrollInertia: 200
      });
    }
  }
}


function open_add_idea_form(){
  if($('.modal-home-add-idea').length == 0){
    $(document.body).append('<div class="modal-backdrop fade in modal-home-add-idea"></div>')
  }
  $(".home-add-idea").css("position","relative");
  $(".home-add-idea .form-group:not(.idea-text),"+
     ".home-add-idea .form-group label,"+
     ".home-add-idea .form-group.idea-text #desc").slideDown();
    $(".home-add-idea").addClass('opened').removeClass('closed')
}

function close_add_idea_form(){
  var add_idea_form = $(".home-add-idea")
  add_idea_form.css("position","inherit");
  var form_groups = add_idea_form.find('.form-group')
  form_groups.removeClass('has-error')
  form_groups.find('p.help-block.help-error').remove()
  
  $('.modal-home-add-idea').remove()
   $(".home-add-idea .form-group:not(.idea-text),"+
     ".home-add-idea .form-group label,"+
     ".home-add-idea .form-group.idea-text #desc").slideUp();
    add_idea_form.addClass('closed').removeClass('opened')
    $(".similar-ideas.modal").modal('hide')
    $(".home-add-idea .btn").removeClass('active')
  }


function display_carousel(){
  var slider =  $($(this).parents('.file-slider').first())
  var clone = slider.clone()
  $(clone.find('div.img-content')).each(function(){
     var imgurl = $($(this).parents('a').first()).attr('href')
     $(this).replaceWith('<img class="img-content" src="'+imgurl+'"/>')
  })

  clone.addClass('full')
  var car_id = $(clone.find('.carousel.slide')).attr('id')
  var new_id = car_id+'-full'
  var controls = clone.find('a.carousel-control[href="#'+car_id+'"]')
  $(clone.find('.carousel.slide')).attr('id', new_id)
  controls.attr('href', '#'+new_id)
  var modal_container = $('#carousel-img-modal-container')
  $(modal_container.find('.modal-body')).html(clone);
  var title = get_comment_author_bloc($(this))
  if(title.length == 0){
    title = $($(this).parents('.view-item, .content-view').first().find('.view-item-title, .content-title').first()).clone()
    title.find('.label-basic').remove()
    title = $(title.find(':header').first()).html()
  }

  $(modal_container.find('.modal-title')).html(title)  
  modal_container.css('opacity', '1')
  modal_container.modal('show');
  $('#' + new_id).carousel({
    interval: false
  })
  return false
}


function get_comment_author_bloc(element){
  var comment_data = $(element.parents('.comment-data').first())
  var clone = $(comment_data.clone())
  clone.find('.comment-content>div').not('.comment-author').remove()
  clone.removeClass('comment-data')
  return clone
}


function alert_user_unread_messages(){
  var is_unread = $('.all-channels.toggled .unread-comments-len').length > 0
  if (is_unread){
    var alert = $('.all-channels-toggle:not(.close) #alert-message')
    setTimeout(function(){alert.show().fadeOut(4000)}, 1000);
  }
}


function unsubscribe_user_from_alerts(alerts){
    var alert_content = $(alerts.find('.alerts-content'))
      if(!alert_content.hasClass('hide-bloc')){
        var url = alert_content.data('unsubscribe_url')
        $.getJSON(url,{}, function(data) {
          if(data.status){
            alerts.addClass('off')
          }
        });
      }
}


$(document).on('click', '.full-screen-btn.small', function(){
    var $this = $(this)
    $('.pontus-main').addClass('full-screen');
    $this.removeClass('glyphicon glyphicon-resize-full').addClass('glyphicon glyphicon-resize-small')
    $this.removeClass('small').addClass('full')
    $('.pontus-main').removeClass('small').addClass('full')

});

$(document).on('click', '.full-screen-btn.full', function(){
    var $this = $(this)
    $('.pontus-main').removeClass('full-screen');
    $this.removeClass('glyphicon glyphicon-resize-small').addClass('glyphicon glyphicon-resize-full')
    $this.removeClass('full').addClass('small')
    $('.pontus-main').removeClass('full').addClass('small')

});

$(document).on('click', '.proposal-opinion', activate_explanation);

$(document).on('click', '.proposal-opinion button.close', close_explanation);

$(document).on('click', '.working-group-toggle', function(){
    var $this = $(this)
      var wg_section_body = $($this.parents('.working-group-result').first().find('.working-group-section').first());
      var btn = $($this.find('.working-group-toggle-btn').first());
      
      if(wg_section_body.hasClass('hide-bloc')){
       btn.addClass('ion-ios7-arrow-up');
        btn.removeClass(' ion-ios7-arrow-down');
        wg_section_body.removeClass('hide-bloc');
      }else{
        btn.removeClass('ion-ios7-arrow-up');
        btn.addClass(' ion-ios7-arrow-down');
        wg_section_body.addClass('hide-bloc');
      };
      
      init_result_scroll();
        
  });


$(document).on('click', '.proposal-support .token:not(.disabled)', function(){
   var $this = $(this)
   var action_url = $this.data('action')
   var url_attr = get_action_metadata($($this.parents('.proposal-support').first()))
   if(action_url){
     loading_progress()
     $.post(action_url,url_attr, function(data) {
          finish_progress()
          data.token_action = $this.hasClass('token-success')? 'token-success': 'token-danger';
          update_components(data)
        });
   }

})

$(document).on('click', '.sidebar-nav li > a.primary', function(event){
    var $this = $(this)
    if(!event.internal){
      $this.addClass('current')
      var menuevent = jQuery.Event( "click" );
      menuevent.internal = true;
      $('.sidebar-nav li > a.primary.active-item:not(.current)').trigger(menuevent);
      $this.removeClass('current')
    }
    var iconstate = $($this.find('span.icon-state'));
    if(iconstate.hasClass('ion-chevron-down')){
       iconstate.addClass('ion-chevron-up')
       .removeClass('ion-chevron-down')
    }else{
      iconstate.addClass('ion-chevron-down')
       .removeClass('ion-chevron-up')
    }
    if($this.hasClass('active-item')){
       $this.removeClass('active-item')
    }else{
      $this.addClass('active-item')
    }
    
})

$(document).on('click', '.sidebar-background.toggled', function(){
  $(".menu-toggle.close").click()
  $($(this).find(".comment-form-group.active")).removeClass('active')
})

$(document).on('click', '.sidebar-right-background.toggled', function(){
  $(".menu-right-toggle.close").click()
  $('.dace-action-sidebar.activated').click()
  $('body').removeClass('modal-open')

})


$(document).mouseup(function (e)
{
    var container = $(".home-add-idea, .select2-results");
    if (!container.is(e.target) // if the target of the click isn't the container...
        && container.has(e.target).length === 0
        && $(e.target).parents('body').length != 0) // ... nor a descendant of the container
    {
        if(!$(".home-add-idea .form-group.idea-text textarea").val()){
           close_add_idea_form()
        }
    }
});


$(document).on('shown.bs.modal', '.modal', function () {
    init_result_scroll(undefined, 1000, $(this));
});

$(document).ready(function(){

  $.notify.addStyle('bootstrap', {
    html: "<div><span data-notify-html='icon'/> <span data-notify-text='text'/></div>"
  });


  init_emoji($('.emoji-container:not(.emojified)'));
  

  $('.home-add-idea.closed > span.icon-idea').on('click', function(){
      $(this).siblings('form').find('.idea-text textarea').click().focus();
  })
  
  $('.hidden-js').css('display', 'none');

  $(document).on('click','form .btn[type="submit"]', function( event ) {
    var $this = $(this)
    $this.parents('form').find('.btn[type="submit"]').removeClass('active')
    $this.addClass('active')
  })

  $(document).on('change','.home-add-idea form input[name="title"], .home-add-idea form select[name="keywords"]', function( event ) {
        var $this = $(this)
        var form = $($this.parents('form').first())
        var title = form.find('input[name="title"]').val();
        var keywords = $(form.find('select[name="keywords"]')).val();
        if ((!title || title == '') && (!keywords || keywords.length == 0)){
          event.preventDefault();
          return
        }
        var parent = $(form.parents('.home-add-idea').first());
        var target = $(parent.find('.similar-ideas'));
        var url = parent.data('url_search')
        $.getJSON(url,{title: title, keywords: keywords}, function(data){
            if(data.body){
              $(target.find('.similar-ideas-container').first()).html(data.body)
              target.modal('show')
            }else{
              target.modal('hide')
            }
        });
       event.preventDefault();
   });

  $(document).on('submit','form.vote-form', send_vote)
  
  $(document).on('submit','.home-add-idea form', function( event ) {
        var $this = $(this)
        if($this.hasClass('pending')){
          event.preventDefault();
          return
        }
        $this.addClass('pending')
        var button = $($this.find('button.active').first())
        button.addClass('disabled')
        if(button.val() == 'Cancel'){
          $this.find('textarea[name="text"]').val('');
          $this.find('.deform-close-button').click()
          button.removeClass('active');
          button.removeClass('disabled');
          $this.removeClass('pending')
          close_add_idea_form()
          event.preventDefault();
           return
        }
        var parent = $($this.parents('.home-add-idea').first());
        var title = $this.find('input[name="title"]').val();
        var text = $this.find('textarea[name="text"]').val();
        var keywords = $($this.find('select[name="keywords"]')).val();
        if(title=='' || text=='' || !keywords || keywords.length == 0){
          var form_groups = $this.find('.form-group')
          form_groups.removeClass('has-error')
          form_groups.find('p.help-block.help-error').remove()
          var input = null;
          var error_help = '<p class="help-error help-block">'+novaideo_translate("Required") +'</p>'
          alert_component({
            alert_msg: novaideo_translate("There was a problem with your submission."),
            alert_type: 'error'
          })
          if (title=='')
          {
            form_group = $this.find('input[name="title"]').parents('.form-group').first()
            form_group.addClass('has-error')
            form_group.append($(error_help))
          }
          
          if (text=='')
          {
             form_group = $this.find('textarea[name="text"]').parents('.form-group').first()
             form_group.addClass('has-error')
             form_group.append($(error_help))
          }

          if (!keywords || keywords.length == 0)
          {
             form_group = $this.find('select[name="keywords"]').parents('.form-group').first()
             form_group.addClass('has-error')
             form_group.append($(error_help))
          }
          button.removeClass('active');
          button.removeClass('disabled');
          $this.removeClass('pending')
          event.preventDefault();
          return
        }
        
        var formData = new FormData($(this)[0]);
        formData.append(button.val(), button.val())
        var action_metadata = get_action_metadata(button)
        for(key in action_metadata){
            formData.append(key, action_metadata[key])
        }
        var url = parent.data('url')
        var buttons = $($this.find('button'))
        buttons.addClass('disabled');
        loading_progress()
        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(data) {
              var redirect_url = data.redirect_url && !data.ignore_redirect
              if(data.status && !redirect_url){
                    $(data.new_obj_body).hide().prependTo($('.result-container')).fadeIn(1500)
                    init_result_scroll()
              }
              $this.find('input[name="title"]').val(data['new_title']);
              $this.find('textarea[name="text"]').val('');
              $this.find('.deform-close-button').click()
              buttons.removeClass('disabled');
              button.removeClass('active');
              $this.removeClass('pending')
              close_add_idea_form()
              update_components(data)
              if(!redirect_url){
                  finish_progress()
              }
             }
        });


       event.preventDefault();
   });

  $(".home-add-idea.closed .form-group.idea-text").click(function(e) {
      open_add_idea_form()
  });

  $(".menu-toggle").click(function(e) {
        e.preventDefault();
        $(".bar-wrapper").toggleClass("toggled");
        $('.sidebar-background').toggleClass("toggled");
    });

  $(".all-channels-toggle").click(function(e) {
        e.preventDefault();
        $(".all-channels").toggleClass("toggled");
        reset_cookie_channels_bar()
    });

   $(".menu-right-toggle").click(function(e) {
        e.preventDefault();
        var bar = $(".bar-right-wrapper")
        var open = bar.hasClass('toggled')
        bar.toggleClass("toggled");
        $('.sidebar-right-background').toggleClass("toggled");
        $('body').toggleClass('modal-open')
        if(!open){
          $('.dace-action-sidebar.activated').click()
          $(bar.find(".comment-form-group.active")).removeClass('active')

        }
    });

  $(".navbar-toggle.collapsed").on('click', collapse_current_collpsein);

  $('input, textarea').placeholder();

  rebuild_scrolls()
  
  $(window).scroll(function(){
    init_channels_top()
  })

  set_visited();

  init_content_text();

  init_result_scroll();

  init_morecontent_scroll();

  initscroll();

  init_channels_scroll();

  init_channels_top()

  $('nav a nav-control').on('click', function(){
      $(".navbar-toggle").click();
  });

  $(document).on('hide.bs.collapse', '.panel-collapse', function () {
    $(this).siblings().find('a span.glyphicon-minus').attr('class', 'glyphicon glyphicon-plus');
  });

  $(document).on('shown.bs.collapse', '.panel-collapse', function () {
    $(this).siblings().find('a span.glyphicon-plus').attr('class', 'glyphicon glyphicon-minus');
    init_result_scroll(undefined, 1000, $(this));
  });

  // more_content($('.more-content-carousel.verticla'), true);
  // more_content($('.more-content-carousel:not(.vertical)'), false);

  $('.alert-block:not(.off)').hover(function(){
        var $this = $(this);
        var url = $this.data('url');
        var alert_content = $($this.find('.alerts-content').first());
        var target = $(alert_content.find('.content').first());
        alert_content.find('.loading-indicator').removeClass('hide-bloc')
        alert_content.removeClass('hide-bloc');
        $.getJSON(url,{}, function(data) {
          if(data['body']){
            target.html(data['body']);
            alert_content.find('.loading-indicator').addClass('hide-bloc')
            setTimeout(function(){
              unsubscribe_user_from_alerts($this)
            }, 500)
          }
        });

    }, function(){
        var $this = $(this);
        $this.find('.alerts-content').addClass('hide-bloc')
    });

  scroll_to_panel()

  $(document).on('shown.bs.tab', '.nav-tabs',init_result_scroll)

  $(document).on('show.bs.modal', '.similar-ideas', function(){
      $('body').addClass('similar-ideas-modal-open')
  })
  $(document).on('hidden.bs.modal', '.similar-ideas', function(){
      $('body').removeClass('similar-ideas-modal-open')
  })

  $(document).on('click', 'ul.judgment-radio .radio', function(){
      $($(this).find('input')).prop( "checked", true );
  })

   $(document).on('mouseover', '.toggle-popover:not(.active)', function(){
        var $this = $(this);
         $('.comme-popover').remove()
        $this.addClass('active')
        var body = $(document.body)
        var url = body.data('api_url')
        var oid = $this.data('oid');
        setTimeout(function(){
          var has_popover = $this.find('.popover').length > 0
          if($this.hasClass('active') && !has_popover){
            $.getJSON(url,{oid: oid, op: 'get_entity_popover'}, function(data) {
              if(data['body']){
                var popover = $(data['body'])
                $this.append(popover);
                var position = $this.offset()
                popover.css('top', position.top-$(document).scrollTop()-(popover.height()/2)+'px')
                popover.css('left', position.left+$this.width()-2+'px')
                popover.css('display', 'block')
              }
            });
          }
        }, 900);
        

    });

   $(document).on('mouseleave', '.toggle-popover.active', function(){
        var $this = $(this);
        var oid = $this.data('oid');
        $this.removeClass('active')
        $('.comme-popover').remove()
    });

  $(document).on('click', 'a.popover-title-link', function(event){
      event.stopPropagation()
      window.location.replace($(this).attr('href'))
  })

  $('.btn-sub-menu-container').hover(function(){
    var $this = $(this)
    $this.addClass('active')
    $($this.find('ul.btn-sub-menu li')).fadeIn( "fast" )
    $(document.body).append('<div class="modal-backdrop fade in modal-sub-menu"></div>')
    }, function(){
      var $this = $(this)
      $this.removeClass('active')
      $('.modal-sub-menu').remove()
      $($this.find('ul.btn-sub-menu li')).fadeOut( "fast" )
    })

  $(document).on('click', 'a.emoji-group-tab', function(){
      var $this = $(this);
      $('a.emoji-group-tab').removeClass('active')
      $this.addClass('active')
      var group_id = $this.data('group_id')
      var container = $($this.parents('.emoji-anchors').siblings('.emoji-groups').first())
      var group = $(container.find('#'+group_id).first())
      var mCSB_container = $(container.find('.mCSB_container').first())
      if(mCSB_container.length>0){
        container.mCustomScrollbar('scrollTo',group.position().top);
      }else{
        var top = container.scrollTop()+group.position().top -20;       
        container.animate({ scrollTop: top}, 800);
      }
  })

  $(document).on('mouseover', '.emoji-groups .emoji-outer', function(){
      var $this = $(this);
      var groups = $($this.parents('.emoji-groups').first());
      var preview = $(groups.siblings('.emoji-preview').first())
      var img = $($this.find('.emoji-inner').first())
      preview.find('.emoji-preview-img').html(img.clone())
      preview.find('.emoji-preview-title').html(img.attr('title').replace(/-|_/g, ' '))
      preview.find('.emoji-preview-symbol').html(':'+img.attr('title')+':')

    });

   $(document).on('mouseleave', '.emoji-groups .emoji-outer', function(){
      var $this = $(this);
      var groups = $($this.parents('.emoji-groups').first());
      var preview = $(groups.siblings('.emoji-preview').first())
      preview.find('.emoji-preview-img').html('')
      preview.find('.emoji-preview-title').html('Emoji')
      preview.find('.emoji-preview-symbol').html('')

    });

  $(document).on('click', '.files-block .deform-seq-add', function(){
    $($(this).parents('.files-block').first().find('input[type="file"]').last()).click()
  })

  $(document).on('change', '.files-block input[type="file"]', function(){
    $($(this).parents('.deform-seq-item').first()).addClass('uploaded')
   })

  $(document).on('click', 'form button[type="submit"]', function(){
    $($(this).parents('form').first().find('.deform-seq-item:not(.uploaded)').find('.deform-close-button')).click();

  })

  $(document).on('click', 'a.channel-action', function(){
    var channel_action = $($(this).parents('div.channel-action').first())
    $(channel_action.find('.unread-comments-len')).remove()
    channel_action.removeClass('unread-comments')
    update_unread_messages_alerts()
  });

  focus_on_form($('.pontus-main'))

  $(document).on('click', '.file-slider:not(.full) .carousel-inner a', display_carousel)

  alert_user_unread_messages()
  update_unread_messages_alerts()
  
  $(document).on('click', '.alert-messages-scroll', scroll_to_unread_message)
  
});


var alert_unread_messages_bottom_pt = '<div class="alert-messages-scroll down">'+
  '<span class="fa fa-long-arrow-down"></span> <span>'+novaideo_translate('Unread messages')+'</span> '+
  '<span class="fa fa-long-arrow-down"></span></div>'

var alert_unread_messages_top_pt = '<div class="alert-messages-scroll top">'+
  '<span class="fa fa-long-arrow-up"></span> <span>'+novaideo_translate('Unread messages')+'</span> '+
  '<span class="fa fa-long-arrow-up"></span></div>'


function scroll_to_unread_message(){
  var target = $($(this).data('target'))
  var channel_action = $(target.parents('.channel-action').first())
  var scrollable = $(channel_action.parents('.channels-container').first())
  //scroll if mCS
  scrollable.mCustomScrollbar("scrollTo",channel_action,{
        scrollInertia: 200,
        callbacks:{
          onScroll:function(){
            update_unread_messages_alerts()
          }
        }
      })
  //scroll if not mCS
  var top = scrollable.scrollTop() + channel_action.position().top-100;      
  scrollable.animate({ scrollTop: top}, 1000);

}

function update_unread_messages_alerts(){
  var channels = $('.channels-container')
  channels.each(function(){
     var has_unread = has_hidden_unread_messages($(this))
     $($(this).parents('.channels-block').find('.alert-messages-scroll')).remove()
     if(has_unread.top){
       var alert_obj = $(alert_unread_messages_top_pt)
       alert_obj.data('target', '#'+result.target_bottom)
       alert_obj.attr('data-target', '#'+result.target_bottom)
       alert_obj.insertAfter($(this))
     }
     if(has_unread.bottom){
       var alert_obj = $(alert_unread_messages_bottom_pt)
       alert_obj.data('target', '#'+result.target_top)
       alert_obj.attr('data-target', '#'+result.target_top)
       alert_obj.insertBefore($(this))
     }
  })
}


function has_hidden_unread_messages(channel){
  var unread = $(channel.find('.channel-action .unread-comments-len'))
  result = {'top': false, 'bottom': false}
  if (unread.length > 0){
   for(var i=0; i< unread.length; i++){
     var element = $($(unread[i]).parents('.channel-action').first())
     var is_visible = is_visible_into_view(element, channel)
     result.top = result.top || !is_visible.top
     result.bottom = result.bottom || !is_visible.bottom
     if(!result.target){
      if(!is_visible.top ){
        result.target_bottom = $(element.find('a').first()).attr('id')
      }
      if(!is_visible.bottom ){
        result.target_top = $(element.find('a').first()).attr('id')
      }
     }
   }
  }
  return result
}


function is_visible_into_view(elem, scrollable)
{
    var docViewTop = 0
    var elemTop = 0
    var mCSB_container = $(scrollable.find(".mCSB_container"))
    if(mCSB_container.length > 0){
      docViewTop = (parseInt(mCSB_container.css('top').replace('px', '')) * -1);
      elemTop =  $(elem).offset().top - mCSB_container.offset().top;
    }else{
      docViewTop = scrollable.scrollTop();
      elemTop =  $(elem).position().top;
    }
    var docViewBottom = docViewTop + scrollable.height();
    var elemBottom = elemTop + $(elem).height();

    return {'bottom': (elemBottom <= docViewBottom),
            'top': (elemTop >= docViewTop)}
}



//code adapted from http://bootsnipp.com/snippets/featured/jquery-checkbox-buttons
$(function () {
    $('.search-choices .checkbox-inline').each(function () {

        // Settings
        var $widget = $(this),
            $checkbox = $widget.find('input:checkbox'),
            $button = $('#search-choice-'+$checkbox.attr('value')),
            color = $button.data('color'),
            settings = {
                on: {
                    icon: 'glyphicon glyphicon-check'
                },
                off: {
                    icon: 'glyphicon glyphicon-unchecked'
                }
            };

        // Event Handlers
        $button.on('click', function () {
            $checkbox.prop('checked', !$checkbox.is(':checked'));
            $checkbox.triggerHandler('change');
            updateDisplay();
        });
        $checkbox.on('change', function () {
            updateDisplay();
        });

        // Actions
        function updateDisplay() {
            var isChecked = $checkbox.is(':checked');

            // Set the button's state
            $button.data('state', (isChecked) ? "on" : "off");

            // Set the button's icon
            $button.find('.state-icon')
                .removeClass()
                .addClass('state-icon ' + settings[$button.data('state')].icon);

            // Update the button's color
            if (isChecked) {
                $button
                    .addClass('active');
                $('#'+$button.attr('id')+'-icon').removeClass('hide-bloc')
            }
            else {
                $button
                    .removeClass('active')
                $('#'+$button.attr('id')+'-icon').addClass('hide-bloc')
            }
        }

        // Initialization
        function init() {

            updateDisplay();

            // Inject the icon if applicable
            if ($button.find('.state-icon').length == 0) {
                $button.prepend('<i class="state-icon ' + settings[$button.data('state')].icon + '"></i> ');
            }
        }
        init();
    });
});