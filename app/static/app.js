
var app = new Vue({
  el: "#app",

  //------- data --------
  data: {
    serviceURL: "https://cs3103.cs.unb.ca:8015",
    authenticated: false,
    links: null,
    loggedIn: null,
    input: {
      username: "",
      password: ""
    },
    newLink: {
      original_link: ""
    },
  },
  //------- lifecyle hooks --------
  mounted: function() {
    axios
    .get(this.serviceURL+"/login")
    .then(response => {
      if(response.data.status == "success") {
        this.authenticated = true;
        this.loggedIn = response.data.user_id;
        this.getLinks();
      }
    })
    .catch(error => {
        this.authenticated = false;
        console.log(error);
    });
  },

  //------- methods --------
  methods: {
    login() {
      if (this.input.username != "" && this.input.password != "") {
        axios
        .post(this.serviceURL+"/login", {
          "username": this.input.username,
          "password": this.input.password
        })
        .then(response => {
          if (response.data.status == "success") {
            this.authenticated = true;
            this.loggedIn = response.data.user_id;
            this.getLinks();
          }
        })
        .catch(e => {
          Swal.fire({
            icon: "error",
            title: "Invalid Credentials",
            text: "The username or password is incorrect, try again"
          });
          this.input.password = "";
          console.log(e);
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Missing Credentials",
          text: "A username and password must be present"
        });
      }
    },

    logout() {
      axios
      .delete(this.serviceURL+"/login")
      .then(response => {
        location.reload();
      })
      .catch(e => {
        console.log(e);
      });
    },

    getLinks() {
      axios
      .get(this.serviceURL+"/links")
      .then(response => {
          this.links = response.data.links;
      })
      .catch(e => {
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Unable to load the links data"
        });
        console.log(e);
      });
    },

    findLink(id) {
      var link = null;
      var index = -1;
      for (x in this.links) {
        if (this.links[x].id == id) {
          link = this.links[x];
          index = x;
        }
      }
      return [link, index];
    },

    createLink() {
      if(this.newLink.original_link != "") {
        axios
        .post(this.serviceURL+"/links", {
          "original_link": this.newLink.original_link
        })
        .then(response => {
          if(response.data.status == 'success') {
            this.links.push(response.data.link);
            console.log(response.data.link);
            this.newLink.original_link = "";
          }
        })
        .catch(e => {
          Swal.fire({
            icon: "error",
            title: "Failed to Create Link",
            text: "Please ensure you entered a valid link and try again"
          });
          console.log(e);
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Missing Link",
          text: "Please enter a link to shorten"
        });
      }
    },

    deleteLink(id) {
      var link = this.findLink(id);
      Swal.fire({
        icon: "warning",
        title: "Confirm Deletion",
        html: "Are you sure you want to delete link <strong>"+link[0].shortened_link+"</strong>?",
        showCancelButton: true,
        cancelButtonColor: "#6c757d",
        confirmButtonColor: "#dc3545",
        confirmButtonText: "Delete it!"
      }).then((result) => {
        if(result.isConfirmed) {
          axios
          .delete(this.serviceURL+"/links/"+id)
          .then(response => {
            if(response.status == 204) {
              var link = this.findLink(id);
              this.links.splice(link[1], 1);
            }
          })
          .catch(e => {
            console.log(e);
          });
        }
      });
    },

    enableEditLink(id) {
      var fld = $("#update-fld-"+id);
      fld.prop("disabled", false);
      fld.data("original", fld.val());
      fld.focus();

      var btn = $("#update-btn-"+id);
      btn.removeClass("hidden");
    },

    disableEditLink(id, updated) {
      var fld = $("#update-fld-"+id);
      if(!updated) {
        fld.val(fld.data("original"));
      }
      fld.prop("disabled", true);
      fld.removeData("original");

      var btn = $("#update-btn-"+id);
      btn.addClass("hidden");
    },

    updateLink(id) {
      var link = this.findLink(id);
      link = link[0];

      if(link.original_link != "") {
        axios
        .patch(this.serviceURL+"/links/"+id, {
          "original_link": link.original_link
        })
        .then(response => {
          if(response.data.status == "success") {
            this.disableEditLink(id, true);
          }
        })
        .catch(e => {
          Swal.fire({
            icon: "error",
            title: "Failed to Update Link",
            text: "Please ensure you entered a valid link and try again"
          });
          console.log(e);
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Missing Link",
          text: "Please enter a link to shorten"
        });
      }
    },

    copyLink(id) {
      link = this.findLink(id);
      link = link[0];
    
      var url = this.serviceURL+"/l/"+link.shortened_link;

      var temp = $("<input>");
      $("body").append(temp);
      temp.val(url).select();
      document.execCommand("copy");
      temp.remove();

      Swal.fire({
        icon: "success",
        title: "Link Copied!",
        text: url,
        showConfirmButton: false,
        timer: 1500
      });

    },

  }
  //------- END methods --------

});

