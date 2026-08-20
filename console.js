(async () => {
  const options = {
    includePrivateProfiles: false,
    emailFormat: null,
    promptForEmailFormat: true,
    pageSize: 10,
    maxResults: 1000,
    jitter: false,
    downloadJson: true,
    downloadCsv: true,
    logRows: true,
  };

  const BAD_WORDS = new Set(["Prof.", "Dr.", "M.A.", ",", "LL.M."]);
  const SPECIAL_CHAR_MAP = {
    ae: /ä/g,
    oe: /ö/g,
    ue: /ü/g,
    ss: /ß/g,
  };

  function getCookie(name) {
    const parts = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
    if (!parts) return null;
    return decodeURIComponent(parts.split("=").slice(1).join("=")).replace(/^"|"$/g, "");
  }

  function companySlugFromUrl() {
    const match = window.location.href.match(/linkedin\.com\/company\/([^/?#]+)/i);
    if (!match) {
      throw new Error("Open a LinkedIn company page first, e.g. https://www.linkedin.com/company/example");
    }
    return decodeURIComponent(match[1]);
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function cleanText(value) {
    if (!value) return "N/A";
    let cleaned = String(value)
      .replace(
        /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2500}-\u{2BEF}\u{2702}-\u{27B0}\u{24C2}-\u{1F251}\u{1F926}-\u{1F937}\u{10000}-\u{10FFFF}\u2640-\u2642\u2600-\u2B55\u200D\u23CF\u23E9\u231A\uFE0F\u3030]/gu,
        ""
      )
      .trim()
      .replace(/Ü/g, "Ue")
      .replace(/Ä/g, "Ae")
      .replace(/Ö/g, "Oe")
      .replace(/ü/g, "ue")
      .replace(/ä/g, "ae")
      .replace(/ö/g, "oe")
      .replace(/,/g, "")
      .replace(/;/g, ",")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");

    return cleaned.trim() || "N/A";
  }

  function cleanForEmail(value) {
    let cleaned = String(value || "")
      .replace(/\./g, "")
      .trim()
      .toLowerCase();

    cleaned = cleaned
      .replace(SPECIAL_CHAR_MAP.ae, "ae")
      .replace(SPECIAL_CHAR_MAP.oe, "oe")
      .replace(SPECIAL_CHAR_MAP.ue, "ue")
      .replace(SPECIAL_CHAR_MAP.ss, "ss")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");

    return cleaned;
  }

  function applyEmailFormat(template, firstname, lastname) {
    return template.replace(/\{([01])(?:\[(\d+)])?\}/g, (_, slot, index) => {
      const source = slot === "0" ? firstname : lastname;
      if (index !== undefined) {
        return source[Number(index)] || "";
      }
      return source;
    });
  }

  function promptForEmailTemplate() {
    if (options.emailFormat || !options.promptForEmailFormat) {
      return options.emailFormat;
    }

    const structurePrompt = [
      "Email structure for auto-generated emails:",
      "",
      "first.last  -> john.doe@example.com",
      "f.last      -> j.doe@example.com",
      "first       -> john@example.com",
      "last        -> doe@example.com",
      "fl          -> jd@example.com",
      "firstlast   -> johndoe@example.com",
      "last.first  -> doe.john@example.com",
      "custom      -> enter your own placeholder pattern",
      "",
      "Leave blank or press Cancel to skip email generation.",
    ].join("\n");

    const structureInput = window.prompt(structurePrompt, "first.last");
    if (structureInput == null || !structureInput.trim()) {
      return null;
    }

    const structure = structureInput.trim().toLowerCase();
    const templateMap = {
      "first.last": "{0}.{1}",
      "f.last": "{0[0]}.{1}",
      first: "{0}",
      last: "{1}",
      fl: "{0[0]}{1[0]}",
      firstlast: "{0}{1}",
      "last.first": "{1}.{0}",
    };

    let localPartTemplate = templateMap[structure];

    if (structure === "custom") {
      const customTemplate = window.prompt(
        "Enter a custom local-part template using {0} for first name and {1} for last name.\nExamples: {0}.{1} or {0[0]}.{1}",
        "{0}.{1}"
      );
      if (customTemplate == null || !customTemplate.trim()) {
        return null;
      }
      localPartTemplate = customTemplate.trim();
    }

    if (!localPartTemplate) {
      console.warn(`[!] Unknown email structure: ${structureInput}. Skipping email generation.`);
      return null;
    }

    const domainInput = window.prompt("Email domain to append", "example.com");
    if (domainInput == null || !domainInput.trim()) {
      return null;
    }

    const domain = domainInput.trim().replace(/^@+/, "");
    return `${localPartTemplate}@${domain}`;
  }

  function csvEscape(value) {
    const text = value == null ? "" : String(value);
    if (!/[;"\n\r]/.test(text)) return text;
    return `"${text.replace(/"/g, '""')}"`;
  }

  function downloadText(filename, text, mimeType) {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function findItemsArrays(node, acc = []) {
    if (!node || typeof node !== "object") return acc;
    if (Array.isArray(node)) {
      for (const item of node) findItemsArrays(item, acc);
      return acc;
    }
    if (Array.isArray(node.items)) acc.push(node.items);
    for (const value of Object.values(node)) {
      findItemsArrays(value, acc);
    }
    return acc;
  }

  function parseEmployeeResults(results, includePrivateProfiles) {
    const employees = [];

    for (const employee of results) {
      const entity = employee?.itemUnion?.entityResult || employee?.entityResult;
      if (!entity) continue;

      const rawName = cleanText(entity?.title?.text);
      const accountName = rawName
        .split(/\s+/)
        .filter(Boolean)
        .filter((word) => !BAD_WORDS.has(word));

      if (accountName.length === 0) continue;

      const firstname = accountName.length > 2 ? accountName.slice(0, -1).join(" ") : accountName[0];
      const lastname = accountName.length > 1 ? accountName[accountName.length - 1] : "";
      const position = cleanText(entity?.primarySubtitle?.text || "N/A");
      const location = cleanText(entity?.secondarySubtitle?.text || "N/A");
      const profileLink = (entity?.navigationUrl || "N/A").split("?")[0];
      const isPrivateProfile = firstname === "LinkedIn" && lastname === "Member";

      if (!includePrivateProfiles && isPrivateProfile) continue;

      employees.push({
        firstname,
        lastname,
        position,
        gender: "N/A",
        location,
        profile_link: isPrivateProfile ? "N/A" : profileLink,
      });
    }

    return employees;
  }

  function dedupeEmployees(employees) {
    const seen = new Set();
    return employees.filter((person) => {
      const key = [person.firstname, person.lastname, person.profile_link].join("|");
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  async function fetchLinkedInJson(url, csrfToken) {
    const response = await fetch(url, {
      credentials: "include",
      headers: {
        accept: "application/json",
        "csrf-token": csrfToken || "",
        "x-restli-protocol-version": "2.0.0",
      },
    });

    if (!response.ok) {
      throw new Error(`LinkedIn request failed (${response.status} ${response.statusText}) for ${url}`);
    }

    return response.json();
  }

  async function getCompanyId(companySlug, csrfToken) {
    const apiUrl =
      "https://www.linkedin.com/voyager/api/voyagerOrganizationDashCompanies" +
      `?decorationId=com.linkedin.voyager.dash.deco.organization.MiniCompany-10&q=universalName&universalName=${encodeURIComponent(companySlug)}`;
    const data = await fetchLinkedInJson(apiUrl, csrfToken);
    const companyUrn = data?.elements?.[0]?.entityUrn;
    if (!companyUrn) {
      throw new Error("Could not resolve company ID from the current company page.");
    }
    return companyUrn.split(":").pop();
  }

  async function getEmployeeData(companyId, start, count, csrfToken) {
    const apiUrl =
      "https://www.linkedin.com/voyager/api/search/dash/clusters" +
      "?decorationId=com.linkedin.voyager.dash.deco.search.SearchClusterCollection-165" +
      "&origin=COMPANY_PAGE_CANNED_SEARCH" +
      "&q=all" +
      `&query=(flagshipSearchIntent:SEARCH_SRP,queryParameters:(currentCompany:List(${companyId}),resultType:List(PEOPLE)),includeFiltersInResponse:false)` +
      `&count=${count}&start=${start}`;
    return fetchLinkedInJson(apiUrl, csrfToken);
  }

  function buildCsv(employees, includeEmail) {
    const headers = includeEmail
      ? ["Firstname", "Lastname", "Email", "Position", "Gender", "Location", "Profile"]
      : ["Firstname", "Lastname", "Position", "Gender", "Location", "Profile"];

    const lines = [headers.join(";")];

    for (const person of employees) {
      const row = includeEmail
        ? [
            person.firstname,
            person.lastname,
            person.email || "N/A",
            person.position,
            person.gender,
            person.location,
            person.profile_link,
          ]
        : [
            person.firstname,
            person.lastname,
            person.position,
            person.gender,
            person.location,
            person.profile_link,
          ];

      lines.push(row.map(csvEscape).join(";"));
    }

    return lines.join("\n");
  }

  const startedAt = new Date();
  const companySlug = companySlugFromUrl();
  const csrfToken = getCookie("JSESSIONID");
  options.emailFormat = promptForEmailTemplate();
  const companyId = await getCompanyId(companySlug, csrfToken);
  const firstPage = await getEmployeeData(companyId, 0, options.pageSize, csrfToken);
  const pagingTotal = Number(firstPage?.paging?.total || 0);
  const cappedTotal = Math.min(pagingTotal, options.maxResults);
  const totalPages = Math.ceil(cappedTotal / options.pageSize);
  const allEmployees = [];

  console.log(`[i] Company Name: ${companySlug}`);
  console.log(`[i] Company X-ID: ${companyId}`);
  console.log(`[i] LN Employees: ${pagingTotal} employees found`);
  console.log(`[i] Dumping Date: ${startedAt.toLocaleString()}`);
  if (options.emailFormat) {
    console.log(`[i] Email Format: ${options.emailFormat}`);
  }
  if (pagingTotal > options.maxResults) {
    console.warn(`[!] LinkedIn usually caps this search near ${options.maxResults} results. Only the first ${options.maxResults} will be requested.`);
  }

  for (let page = 0; page < totalPages; page += 1) {
    if (options.jitter && page > 0) {
      const delays = [300, 500, 800, 1000, 1500, 3000];
      await sleep(delays[Math.floor(Math.random() * delays.length)]);
    }

    const data = page === 0 ? firstPage : await getEmployeeData(companyId, page * options.pageSize, options.pageSize, csrfToken);
    const itemGroups = findItemsArrays(data);

    for (const results of itemGroups) {
      allEmployees.push(...parseEmployeeResults(results, options.includePrivateProfiles));
    }

    console.log(`[i] Progress: ${page + 1}/${totalPages}`);
  }

  const employees = dedupeEmployees(allEmployees).map((person) => {
    if (!options.emailFormat) return person;

    const firstname = cleanForEmail(person.firstname);
    const lastname = cleanForEmail(person.lastname);
    return {
      ...person,
      email:
        firstname === "linkedin" && lastname === "member"
          ? "N/A"
          : applyEmailFormat(options.emailFormat, firstname, lastname),
    };
  });

  const output = {
    company_id: companyId,
    company_url: window.location.href,
    company_slug: companySlug,
    timestamp: new Date().toISOString(),
    employees,
  };
  const csvText = buildCsv(employees, Boolean(options.emailFormat));

  if (options.logRows) {
    console.table(
      employees.map((person) => ({
        firstname: person.firstname,
        lastname: person.lastname,
        email: person.email || "",
        position: person.position,
        gender: person.gender,
        location: person.location,
        profile: person.profile_link,
      }))
    );
  }

  if (options.downloadJson) {
    downloadText(
      `${companySlug}.json`,
      JSON.stringify(output, null, 2),
      "application/json;charset=utf-8"
    );
  }

  if (options.downloadCsv) {
    downloadText(
      `${companySlug}.csv`,
      csvText,
      "text/csv;charset=utf-8"
    );
  }

  console.log(`[i] Successfully crawled ${employees.length} unique ${companySlug} employee(s).`);
  window.LinkedInDumper = output;
  window.LinkedInDumperCsv = csvText;
  window.downloadLinkedInDumperCsv = () =>
    downloadText(`${companySlug}.csv`, window.LinkedInDumperCsv, "text/csv;charset=utf-8");
  window.downloadLinkedInDumperJson = () =>
    downloadText(`${companySlug}.json`, JSON.stringify(window.LinkedInDumper, null, 2), "application/json;charset=utf-8");
  return output;
})();
