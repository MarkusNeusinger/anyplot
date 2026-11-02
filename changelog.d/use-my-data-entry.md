### Changed

- **The plot page's way into "use with my data" is a text action beside the
  library carousel.** `.use_my_data() →` sits to the right of the carousel as
  the mirror of `← .compare()` on its left and replaces the data-table icon on
  the image, which said little and crowded the overlay buttons. It keeps the
  icon's gating (open lane or an admin, eligible pair), its chat link and
  `agent_open`'s `source=plot_page`; "experimental" is left to the chat's
  notice. The carousel now sits centred over the image, so the action fades
  in after the eligibility check without moving anything; on a phone or
  tablet the two actions share the line above the carousel (#12539).
- **The landing page's line points to the catalogue.** While the public lane
  is open it reads `# new: pick any plot, then .use_my_data() →` and leads to
  `/plots` instead of opening the chat on one fixed plot, tracked as
  `nav_click{source: hero_use_my_data}` (#12539).
