window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};

const venueDeleteBtn = document.getElementById("venue-del-btn");

venueDeleteBtn.addEventListener("click", () => {
  const venueId = venueDeleteBtn.dataset["id"];
  console.log(venueId);
  const url = `/venues/${venueId}`;
  fetch(url, { method: "DELETE" })
    .then((response) => {
      if (response.redirected) {
        window.location.href = response.url;
      }
    })
    .catch((err) => console.log(err));
});
