function loginUser(e) {
      e.preventDefault();

      // kuhaon ang values (optional for now)
      let email = document.querySelector('input[type="email"]').value;
      let password = document.querySelector('input[type="password"]').value;

      // simple validation (optional)
      if (email === "" || password === "") {
        alert("Please fill in all fields");
        return;
      }

      // SET LOGIN STATE
      localStorage.setItem("loggedIn", "true");

      // alert("Login successful!");

      // redirect to home page
      window.location.href = "/assessment";
    }