
$( document ).ready(function() {
    // user role and field management.
    
    const all_fields = ["first_name", "middle_name", "last_name",
    "gender", "dob", "phone", "email", "occupation", "cur_position", "work_exp",
    "picture", 
    "high_education", "domain_exp", "edu_level", "institution_name", "institution_place",
    "country", "state", "location", "assess_pack_alloc",
    "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc",
    "contact_address", "perm_address", "off_address",
    "user_bio", "group_name", "org_name", "manager_name", "pan_tan",
    "emp_id", "div_region", "ga_permissions",
    "chp_agency_name", "chp_region", "chp_agrmt_id", "chp_contr_period", "category", "rate"];
    // ["first_name", "middle_name", "last_name",
    //     "gender", "dob", "phone", "occupation", "cur_position", "work_exp",
    //     "high_education", "domain_exp", "edu_level", "institution_name", "institution_place",
    //     "country", "state", "location", "assess_pack_alloc",
    //     "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc",
    //     "contact_address", "perm_address",
    //     "user_bio", "group_name", "org_name", "manager_name", "pan_tan", "off_address",
    //     "chp_agrmt_id", "chp_contr_period"];

    const role_map = {
        // '0': ['first_name', 'middle_name', 'last_name'],
        '1': ['first_name', 'middle_name', 'last_name', "email"],
        '2': ["first_name", "middle_name", "last_name", "group_name", "org_name", "manager_name", "email", "phone", "pan_tan", "off_address"],
        '3': ["first_name", "middle_name", "last_name", "group_name", "org_name", "manager_name", "email", "phone", "pan_tan", "off_address"],
        '4': ["first_name", "middle_name", "last_name", "gender", "dob", "email", "phone", "occupation", "cur_position", "work_exp", "high_education", "country", "state", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "contact_address", "perm_address"],
        '5': ["first_name", "middle_name", "last_name", "gender", "dob", "email", "phone", "occupation", "cur_position", "work_exp", "high_education", "domain_exp", "country", "state", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "contact_address", "perm_address", "user_bio"],
        '6': ["first_name", "middle_name", "last_name", "gender", "dob", "email", "phone", "occupation", "cur_position", "work_exp", "high_education", "domain_exp", "country", "state", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "contact_address", "perm_address", "user_bio"],
        '7': ["first_name", "middle_name", "last_name", "email", "cur_position", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "chp_agrmt_id", "chp_contr_period"],
        '8': ["first_name", "middle_name", "last_name", "gender", "dob", "email", "phone", "category", "rate", "occupation", "cur_position", "work_exp", "high_education", "domain_exp", "country", "state", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "contact_address", "perm_address", "user_bio"],
        '9': ["first_name", "middle_name", "last_name", "gender", "dob", "email", "phone", "occupation", "cur_position", "work_exp", "high_education", "edu_level", "institution_name", "institution_place", "country", "state", "location", "assess_pack_alloc"],
        '10':["first_name", "middle_name", "last_name", "email", "phone", "cur_position", "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc", "chp_agency_name", "chp_region", "chp_agrmt_id", "chp_contr_period", "contact_address", "perm_address"],
        '11':["first_name", "middle_name", "last_name", "email", "gender", "dob", "phone"],
    };
        
    let role_el = document.getElementById('id_role');
    role_el.addEventListener('change', function(e){
        let role_key = e.target.value;

        // hide all fields.
        for (var i = 0; i < all_fields.length; i++) {
            let el = document.querySelector('#div_id_'+all_fields[i]);
            if (!el.classList.contains('d-none'))
                document.querySelector('#div_id_'+all_fields[i]).classList.add("d-none");
        }

        // show role based fields.
        for (var j = 0; j < role_map[role_key].length; j++) {
            let el = document.querySelector('#div_id_'+role_map[role_key][j]);
            
            if (el.classList.contains('d-none'))
                document.querySelector('#div_id_'+role_map[role_key][j]).classList.remove("d-none");
        }
    });
    
    // trigger change event while first load
    if ("createEvent" in document) {
        var evt = document.createEvent("HTMLEvents");
        evt.initEvent("change", false, true);
        role_el.dispatchEvent(evt);
    } else role_el.fireEvent("onchange");

    // removes the super user role from role list.
    // role_el.options[0].remove();
});
