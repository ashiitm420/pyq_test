function i(e=""){return e.split(" · ").filter(t=>!/\.pdf\b/i.test(t)&&!/^timed practice \(user-selected duration\)$/i.test(t.trim())).join(" · ")||"Practice session"}export{i as d};
