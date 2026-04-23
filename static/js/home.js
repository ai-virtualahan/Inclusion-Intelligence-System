function handleAuth() {
      let isLoggedIn = localStorage.getItem("loggedIn");

      if (isLoggedIn === "true") {
        localStorage.setItem("loggedIn", "false");
        // alert("Logged out successfully!");
        location.reload();
      } else {
        window.location.href = "/login";
      }
    }

    function goToAssessment(e) {
      e.preventDefault();

      let isLoggedIn = localStorage.getItem("loggedIn");

      if (isLoggedIn === "true") {
        window.location.href = "/assessment";
      } else {
        window.location.href = "/login";
      }
    }

    window.onload = function () {
      let btn = document.querySelector(".login-btn");
      let welcome = document.getElementById("welcomeText");
      let startBtn = document.getElementById("startBtn");

      
      updateUI();

      startBtn.onclick = function () {
        let isLoggedIn = localStorage.getItem("loggedIn");

        if (isLoggedIn === "true") {
          window.location.href = "/assessment";
        } else {
          window.location.href = "/login";
        }
      };
    };