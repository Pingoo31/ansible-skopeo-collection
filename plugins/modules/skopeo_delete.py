"""`skopeo_delete` Ansible plugin inside the `local.skopeo` collection.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: skopeo_delete

short_description: Delete a container image from one registry

version_added: "0.1.0"

description:
    - Delete a container image from a container registry.
    - If you need to delete multiple images, use an Ansible loop.
    - Please note that additional output may be returned (e.g. stdout_lines, stderr_lines).

options:
    src_image:
        description: |
            Container image name, usually prefixed by a container transport protocol (e.g. docker://, oci://), from a containre registry.
            Please refer to https://github.com/containers/skopeo/blob/main/docs/skopeo.1.md for more information.
            Example: docker://quay.io/namespace/image:tag
        required: true
        type: str
    src_username:
        description: Username to authenticate to the container registry with.
        required: true
        type: str
    src_password:
        description: Password to authenticate to the container registry with.
        required: true
        type: str
    src_tls_verify:
        description: Enables or disables TLS/HTTPS verification against the destination registry.
        required: false
        default: true
        type: bool

author:
    - Antonio Gravino (@antoniogrv)
"""

EXAMPLES = r"""
- name: delete a container image from registry, without authentication, if possible
  local.skopeo.skopeo_delete:
    src_image: docker://source.io/my/image:tag

- name: delete a container image from registry, as an authenticated users on the registry
  local.skopeo.skopeo_delete:
    src_image: docker://source.io/my/image:tag
    username: my_username
    password: my_password

"""

RETURN = r"""
changed:
    description: Returns "false" if the delete attempt fails; returns "true" otherwise.
    type: bool
    returned: always
    sample: false
return_code:
    description: Return code of the Skopeo execution. Defaults to 0 in case of success.
    type: int
    returned: always
    sample: 0
    
"""

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.skopeo_command import SkopeoCommand


def run_module():
    """Runs the Ansible plugin."""

    OPERATION: str = "delete"

    module_args = dict(
        src_image=dict(type="str", required=True),
        tls_verify=dict(type="bool", required=False, default=True),
        username=dict(type="str", required=False),
        password=dict(type="str", required=False, no_log=True),
    )

    result = dict(changed=False, return_code="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    skopeo_command_args = [
        OPERATION,
        f"--tls-verify={str(module.params['tls_verify'])}",
    ]

    if module.params["username"] and module.params["password"]:
        skopeo_command_args.append(
            f"--creds={module.params['username']}:{module.params['password']}"
        )

    skopeo_command_args.extend(
        [module.params["src_image"]]
    )

    skopeo = SkopeoCommand(command=skopeo_command_args)

    result["return_code"] = skopeo.get_return_code()
    result["stdout_lines"] = skopeo.get_stdout()
    result["stderr_lines"] = skopeo.get_stderr()

    if module.check_mode or skopeo.failed():
        if skopeo.get_return_code() == 1:
            result["changed"] = False
            msg = "Image may not exist or is not stored with a v2 Schema in a v2 registry"
            module.error_as_warning(msg, BaseException(module.params["src_image"]))
            module.exit_json(**result)
        else:
            module.fail_json(skopeo.get_stderr(), **result)
    else:
        result["changed"] = True
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
