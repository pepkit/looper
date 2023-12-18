# Begin looper bash autocomplete
_looper_autocomplete()
{
    local cur prev opts1
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    opts1=$(looper --commands)
    case ${COMP_CWORD} in
        1)
            COMPREPLY=($(compgen -W "${opts1}" -- ${cur}))
            ;;
        2)
            COMPREPLY=()
            ;;
    esac
} && complete -o bashdefault -o default -F _looper_autocomplete looper
# end looper bash autocomplete