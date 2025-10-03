/* global $, localStorage */
const API = {
  list: "/api/pets",
  detail: (id) => `/api/pets/${id}`,
  adopt: "/api/adopt",
  adminAdd: "/api/admin/pets"
};

function serializeForm($form) {
  const o = {};
  const a = $form.serializeArray();
  a.forEach(({name, value}) => {
    if (o[name]) {
      if (!Array.isArray(o[name])) o[name] = [o[name]];
      o[name].push(value || "");
    } else {
      o[name] = value || "";
    }
  });
  // include checked checkboxes not sent when false
  $form.find("input[type=checkbox]").each(function() {
    const name = $(this).attr("name");
    if ($(this).is(":checked") && !o[name]) o[name] = $(this).val() || "true";
  });
  return o;
}

function favKey() { return "pf_favorites"; }
function getFavs() {
  try { return JSON.parse(localStorage.getItem(favKey())) || []; } catch { return []; }
}
function setFavs(arr) { localStorage.setItem(favKey(), JSON.stringify(arr)); $("#fav-count").text(arr.length); }
function addFav(id) { const f = new Set(getFavs()); f.add(String(id)); setFavs([...f]); }
function removeFav(id) { const f = new Set(getFavs()); f.delete(String(id)); setFavs([...f]); }
function isFav(id) { return new Set(getFavs()).has(String(id)); }

function petCard(p) {
  const favActive = isFav(p.id) ? "active" : "";
  return `
    <div class="card pet-card">
      <div class="media" style="background-image:url('${p.photo_url || "/static/img/placeholder.png"}')"></div>
      <div class="body">
        <h3>${p.name}</h3>
        <p class="muted">${p.species} • ${p.breed || "Mixed"} • ${p.age} • ${p.size} • ${p.gender}</p>
        <p class="muted">📍 ${p.city || "—"}, ${p.state || "—"}</p>
        <div class="tags">
          ${p.good_with_kids ? '<span class="tag">Kids OK</span>' : ""}
          ${p.vaccinated ? '<span class="tag">Vaccinated</span>' : ""}
        </div>
        <div class="row space-between">
          <a class="btn btn-small" href="/pets/${p.id}">View</a>
          <button class="btn btn-small btn-fav ${favActive}" data-id="${p.id}">♡ Save</button>
        </div>
      </div>
    </div>
  `;
}

function renderPets(list) {
  const html = list.map(petCard).join("");
  $("#results").html(html || `<div class="empty">No pets found. Try adjusting filters.</div>`);
}

function renderPagination(page, pages) {
  if (pages <= 1) { $("#pagination").empty(); return; }
  const prevDisabled = page <= 1 ? "disabled" : "";
  const nextDisabled = page >= pages ? "disabled" : "";
  const html = `
    <button class="btn btn-small pg-prev" ${prevDisabled}>Prev</button>
    <span class="pg-info">Page ${page} / ${pages}</span>
    <button class="btn btn-small pg-next" ${nextDisabled}>Next</button>
  `;
  $("#pagination").html(html);
  $(".pg-prev").on("click", () => fetchPets(page - 1));
  $(".pg-next").on("click", () => fetchPets(page + 1));
}

function fetchPets(page=1) {
  const params = serializeForm($("#filter-form"));
  params.page = page;
  params.per_page = 8;
  const query = $.param(params);
  $("#results").addClass("loading");
  $.getJSON(`${API.list}?${query}`)
    .done(({items, page, pages}) => {
      renderPets(items);
      renderPagination(page, pages);
    })
    .fail(() => {
      $("#results").html(`<div class="error">Failed to load pets. Try again.</div>`);
      $("#pagination").empty();
    })
    .always(() => $("#results").removeClass("loading"));
}

function openFavorites() {
  const ids = getFavs();
  if (!ids.length) {
    $("#favorites-list").html('<div class="empty">No favorites yet. Click “♡ Save” on pets you like.</div>');
  } else {
    // fetch details in parallel
    Promise.all(ids.map(id => $.getJSON(API.detail(id)).catch(()=>null)))
      .then(results => {
        const valid = results.filter(Boolean);
        $("#favorites-list").html(valid.map(petCard).join(""));
      });
  }
  $("#favorites-modal").addClass("open");
}

$(document).ready(function() {
  // initial fav count
  setFavs(getFavs());

  // load pets on page load
  if ($("#filter-form").length) {
    fetchPets(1);
  }

  // search
  $("#filter-form").on("submit", function(e){
    e.preventDefault();
    fetchPets(1);
  });
  $("#reset-filters").on("click", function(){
    $("#filter-form")[0].reset();
    fetchPets(1);
  });

  // toggle favorites on cards & detail page
  $(document).on("click", ".btn-fav, .add-fav", function() {
    const id = $(this).data("id");
    if (isFav(id)) { removeFav(id); } else { addFav(id); }
    fetchPets($("#pagination .pg-info").length ? Number($(".pg-info").text().split(" ")[1]) : 1);
  });

  // favorites modal
  $("#view-favorites").on("click", function(e){ e.preventDefault(); openFavorites(); });
  $(".modal-close, #favorites-modal").on("click", function(e){
    if (e.target === this) $("#favorites-modal").removeClass("open");
  });

  // adopt form
  $("#adopt-form").on("submit", function(e) {
    e.preventDefault();
    const petId = $(this).data("pet-id");
    const payload = serializeForm($(this));
    payload.pet_id = petId;
    $("#adopt-status").text("Submitting…");
    $.ajax({
      url: API.adopt,
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify(payload)
    }).done(() => {
      $("#adopt-status").text("Application submitted! We’ll reach out soon.");
      this.reset();
    }).fail((xhr) => {
      $("#adopt-status").text(xhr.responseJSON?.error || "Something went wrong.");
    });
  });

  // admin add
  $("#admin-add").on("submit", function(e) {
    e.preventDefault();
    const payload = serializeForm($(this));
    payload.good_with_kids = !!payload.good_with_kids;
    payload.vaccinated = !!payload.vaccinated;
    $("#admin-status").text("Saving…");
    $.ajax({
      url: API.adminAdd,
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify(payload)
    }).done((res) => {
      $("#admin-status").text(`Added! New pet ID: ${res.id}`);
      this.reset();
    }).fail((xhr) => {
      $("#admin-status").text(xhr.responseJSON?.error || "Failed to add pet.");
    });
  });
});
