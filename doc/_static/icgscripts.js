function isMobileNav() {
   // UA/touch detection is stable across address-bar show/hide while scrolling
   var ua = navigator.userAgent || '';
   return window.innerWidth <= 720 ||
          navigator.maxTouchPoints > 0 ||
          /Android|iPhone|iPad|iPod|Mobile/i.test(ua);
}

window.onload = function(){
   if (isMobileNav()) {
      closeNav();
   } else {
      openNav();
      $('#navbutton').css({opacity: 0}).animate({opacity: 1}, 2800);
   }
}

window.onresize = function(){
    if (isMobileNav()) {
      closeNav();
      sizeMobileNav();
    }
}
window.addEventListener('orientationchange', function () {
  closeNav();
  setTimeout(sizeMobileNav, 300);
});

function toTop() {
   $('html, body').animate({ scrollTop: 0 }, 'fast');
}

function doNav() {
  if (isMobileNav()) {
    if (document.body.classList.contains('nav-open')) {
      closeNav();
    } else {
      openNav();
    }
  } else {
    if (document.getElementById("mySidenav").style.width === "350px") {
      closeNav();
    } else {
      openNav();
    }
  }
}

function openNav() {
  if (isMobileNav()) {
    document.body.classList.add('nav-open');
    var side = document.getElementById("mySidenav");
    side.style.width = "";
    side.scrollTop = 0;
    var toc = document.getElementById('toctobj2');
    if (toc) {
      try {
        var d = toc.contentDocument || toc.contentWindow.document;
        if (d && d.documentElement) { d.documentElement.scrollTop = 0; }
        if (d && d.body) { d.body.scrollTop = 0; }
      } catch (e) {}
    }
    document.getElementById("main").style.marginLeft = "0";
    document.getElementById("navbutton").style.marginLeft = "0";
  } else {
    document.body.classList.remove('nav-open');
    document.getElementById("mySidenav").style.width = "350px";
    document.getElementById("main").style.marginLeft = "350px";
    document.getElementById("navbutton").style.marginLeft = "350px";
  }
}

function closeNav() {
  document.body.classList.remove('nav-open');
  document.getElementById("mySidenav").style.width = "0";
  document.getElementById("main").style.marginLeft = "0";
  document.getElementById("navbutton").style.marginLeft = "0";
}

function sizeMobileNav() {
  if (!isMobileNav()) { return; }
  var tocFrame = document.getElementById('toctobj2');
  if (!tocFrame) { return; }
  try {
    var doc = tocFrame.contentDocument || tocFrame.contentWindow.document;
    // Let the iframe grow to its content; the sidebar itself scrolls.
    try {
      if (doc.body && !doc.body.dataset.mobileScrollFixed) {
        var st = doc.createElement('style');
        st.textContent = 'html,body{overflow-y:auto!important;-webkit-overflow-scrolling:touch!important;margin:0;}body{padding-bottom:3em!important;}';
        doc.head.appendChild(st);
        doc.body.dataset.mobileScrollFixed = '1';
      }
    } catch (e) {}
    var minHeight = window.innerHeight <= 500
      ? window.innerHeight
      : Math.round(window.innerHeight * 0.8);
    tocFrame.style.setProperty('height', minHeight + 'px', 'important');
    var side = document.getElementById('mySidenav');
    if (side) { side.style.height = ''; }
  } catch (e) {}
}

var tocFrame = document.getElementById('toctobj2');
if (tocFrame) {
  tocFrame.addEventListener('load', function () {
    sizeMobileNav();
    setTimeout(sizeMobileNav, 300);
    setTimeout(sizeMobileNav, 900);
  });
  setTimeout(sizeMobileNav, 100);
}

function enableTouchScroll(el, getScroller) {
  if (!el) { return; }
  var startY = 0, startTop = 0;
  el.addEventListener('touchstart', function (e) {
    if (e.touches && e.touches.length) {
      startY = e.touches[0].clientY;
      var sc = getScroller();
      startTop = sc ? sc.scrollTop : 0;
    }
  }, {passive: true});
  el.addEventListener('touchmove', function (e) {
    if (!e.touches || !e.touches.length) { return; }
    var sc = getScroller();
    if (!sc) { return; }
    var dy = e.touches[0].clientY - startY;
    var max = Math.max(0, sc.scrollHeight - sc.clientHeight);
    if (max > 0) {
      sc.scrollTop = Math.max(0, Math.min(max, startTop - dy));
      e.preventDefault();
    }
  }, {passive: false});
}

var sideEl = document.getElementById('mySidenav');
enableTouchScroll(sideEl, function () { return sideEl; });
if (tocFrame) {
  try {
    var tdoc = tocFrame.contentDocument || tocFrame.contentWindow.document;
    if (tdoc) {
      enableTouchScroll(tdoc, function () {
        return tdoc.scrollingElement || tdoc.documentElement || tdoc.body;
      });
    }
  } catch (e) {}
}

var f = document.getElementById('toctobj2');
var t = window.location.href;
// have to check against all first-level folders 
if (t.lastIndexOf('flac3d/') > 1){t = t.substring(t.lastIndexOf('flac3d/'))};
if (t.lastIndexOf('common/') > 1){t = t.substring(t.lastIndexOf('common/'))};
if (t.lastIndexOf('pfc/') > 1){t = t.substring(t.lastIndexOf('pfc/'))};
if (t.lastIndexOf('udec/') > 1){t = t.substring(t.lastIndexOf('udec/'))};
if (t.lastIndexOf('3dec/') > 1){t = t.substring(t.lastIndexOf('3dec/'))};
f.src = f.src + '?' + t;

//dynamic swap of swap of logo + name when in code section + set logo-link to 'home' page for code + set "alpha/prerelease" watermark as needed
f = document.getElementById('cornerlogo');
t = window.location.href;
if (t.lastIndexOf('/html/flac3d/') > 0 || t.lastIndexOf('/doc/flac3d/') > 0 || t.lastIndexOf('/flac3d/docproject/') > 0) {
  f.src = f.src.substring(0,f.src.lastIndexOf('/')) + '/flac3d32.png';
  document.getElementById('cornercodename').innerHTML = 'FLAC3D';
  document.getElementById('cornerlink').href = t.substring(0,t.lastIndexOf('/flac3d/')) + '/flac3d/docproject/source/flac3dhome.html';
}
//if (t.lastIndexOf('/html/pfc/') > 0 || t.lastIndexOf('/doc/pfc/') > 0 || t.lastIndexOf('/pfc/docproject/') > 0) {
if (t.lastIndexOf('/html/pfc/') > 0 || t.lastIndexOf('/doc/pfc/') > 0 > 0) {   
  f.src = f.src.substring(0,f.src.lastIndexOf('/')) + '/pfc3d32.png';
  document.getElementById('cornercodename').innerHTML = 'PFC';
  document.getElementById('cornerlink').href = t.substring(0,t.lastIndexOf('/pfc/')) + '/pfc/docproject/source/manual/pfchome.html';
  //special little hack for pfc home page to put alpha tag below splash image - remove when not in alpha
}
//if (t.lastIndexOf('/html/3dec/') > 0 || t.lastIndexOf('/doc/3dec/') > 0 || t.lastIndexOf('/3dec/docproject/') > 0) {    // suspended until third term is understood
if (t.lastIndexOf('/html/3dec/') > 0 || t.lastIndexOf('/doc/3dec/') > 0) {
  f.src = f.src.substring(0,f.src.lastIndexOf('/')) + '/3dec32.png';
  document.getElementById('cornercodename').innerHTML = '3DEC';
  document.getElementById('cornerlink').href = t.substring(0,t.lastIndexOf('/3dec/')) + '/3dec/docproject/source/3dechome.html';
  // var p = document.getElementById('cornerlink').href = t.substring(0,t.lastIndexOf('/3dec/')) + '/_static/prerel.png';   //delete when not in alpha/prerelease
  // document.getElementById('mainbody').innerHTML = '<img src="'+p+'" style="position: absolute; margin-left: 27em; margin-top: 2em;" id="alphatag">' + document.getElementById('mainbody').innerHTML; //delete when not in alpha
}


var navTouchX = 0, navTouchY = 0, navTouchMoved = false;
document.addEventListener('touchstart', function (e) {
  if (e.touches && e.touches.length) {
    navTouchX = e.touches[0].clientX;
    navTouchY = e.touches[0].clientY;
    navTouchMoved = false;
  }
}, {passive: true});
document.addEventListener('touchmove', function (e) {
  if (e.touches && e.touches.length) {
    var dx = e.touches[0].clientX - navTouchX;
    var dy = e.touches[0].clientY - navTouchY;
    if (Math.abs(dx) > 10 || Math.abs(dy) > 10) { navTouchMoved = true; }
  }
}, {passive: true});

document.getElementById("navbutton").onclick = function (e) {
  if (navTouchMoved) { e.preventDefault(); return; }
  doNav();
}

//document.getElementById("totopbutton").onclick = function() { toTop(); }

//the iffyness
if ($('#pagecodeid').length > 0){
   if ($('#pagecodeid').html() == "common") {
      codeis = $('#codeid')[0].innerHTML; //common pages derive code from build
   } else {
      codeis = $('#pagecodeid').html();   //non-common pages derive code from tag
   }
   console.log(codeis);
   //codeis = $('#pagecodeid').html();
   
   //swap codename into span tags as needed
   $('span.codeis').text(codeis);
   //cleanup classname as needed
   if (codeis != '3DEC') {codeclass = '.' + codeis.toLowerCase();} //all but 3dec
   if (codeis == '3DEC') {codeclass = '.dec';}  //can't start a class name with a digit
   //show divs
   $('div'+codeclass).css('display', 'block');
   //show spans
   $('span'+codeclass).css('display', 'inline');
   }


//show ids of and around clicked object
$('h1,h2,h3,h4,.h1,.h2,.h3,.h4,table,p').dblclick(function() {
   // 0- only run if on local machine
   if(window.location.href.indexOf("/wad700/") == -1) {
      return;
      }
   // 1- check if uilib is loaded, load ONCE if not
   var head_tag = document.getElementsByTagName("head")[0];
   if (head_tag.innerHTML.indexOf("jquery-ui.js") == -1) {
      $(this).prop('title', 'That was the first double-click');
      var script_tag = document.createElement('script');
      script_tag.setAttribute("src", "https://code.jquery.com/ui/1.12.1/jquery-ui.js");
      head_tag.appendChild(script_tag);
      var link_tag = document.createElement('link');
      link_tag.setAttribute("rel", "stylesheet");
      link_tag.setAttribute("href", "https://code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css");
      head_tag.appendChild(link_tag);
      $("<style type='text/css'> .superlocal{ font-size:1em; font-family: unset;} </style>").appendTo("head");
      return;
      } else {
      $(this).prop('title', ' ');
      };
   // 2- get info and put in dialog
   var par = (this.parentElement) ? [this.parentElement.tagName, this.parentElement.id] : ['none', '(n/a)'] ;
   var pre = (this.previousElementSibling) ? [this.previousElementSibling.tagName, this.previousElementSibling.id] : ['none', '(n/a)'] ;
   var nex = (this.nextElementSibling) ? [this.nextElementSibling.tagName, this.nextElementSibling.id] : ['none', '(n/a)'];
   var chi = (this.firstElementChild) ? [this.firstElementChild.tagName, this.firstElementChild.id] : ['none', '(n/a)'];
   
   var f = '\xa0\u2196\xa0\xa0' + par[0] + ": " + par[1] +  '<br>' + 
           '\xa0\u2191\xa0\xa0' + pre[0] + ": " + pre[1] + '<br>' +
           '\u2192 '+ this.tagName + ': ' + this.id + '<br>' + 
           '\xa0\u2193\xa0\xa0' + nex[0] + ": " + nex[1] + '<br>' +
           '\xa0\u2198\xa0\xa0' + chi[0] + ": " + chi[1] ;
   $( "<div>" + f + "</div>" ).dialog({
     title: "Local IDs",
     width: 400,
     dialogClass: 'superlocal'
     });
  });
  
//change target of wth if page is in code to prevent attempt to open new tab
//if(window.location.href.indexOf("/doc/") == -1){alert('fred')}

