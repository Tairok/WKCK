import {API} from "./api.js";
import { state } from "./state/state.js";

export function bindUI() {
  $(document).on("click", "[data-tab]", function () {
    setTab($(this).data("tab"));
  });

  console.log("UI bindings ready");
}

function setTab(tab) {
  state.activeTab = tab;

  $("[data-tab]").each(function () {
    $(this).toggleClass("active", $(this).data("tab") === tab);
  });

  $("[data-view]").each(function () {
    $(this).toggleClass("active", $(this).data("view") === tab);
  });
}
