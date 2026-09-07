from deidentify.base import Annotation, Document

def apply_surrogates(text, annotations, surrogates, errors='raise'):
    adjusted_annotations = []
    # Amount of characters by which start point of annotation is adjusted
    # Positive shift if surrogates are longer than original annotations
    # Negative shift if surrogates are shorter
    shift = 0
    original_text_pointer = 0
    text_rewritten = ''

    failed_replacements = []

    for annotation, surrogate in zip(annotations, surrogates):
        if not surrogate:
            if errors == 'raise':
                # raise ValueError(f'No valid surrogate for {annotation}')
                surrogate = ""
            if errors == 'ignore':
                surrogate = annotation.text
            elif errors == 'coerce':
                surrogate = f'[{annotation.tag}]'
            failed_replacements.append(annotation)

        part = text[original_text_pointer:annotation.start]

        start = annotation.start + shift
        end = start + len(surrogate)
        shift += len(surrogate) - len(annotation.text)

        adjusted_annotations.append(Annotation(
            text=surrogate,
            start=start,
            end=end,
            tag=annotation.tag,
            doc_id=annotation.doc_id,
            ann_id=annotation.ann_id
        ))

        text_rewritten += part + surrogate
        original_text_pointer = annotation.end

    text_rewritten += text[original_text_pointer:]
    doc_rewritten = Document(name='', text=text_rewritten, annotations=adjusted_annotations)
    doc_rewritten.annotations_without_surrogates = failed_replacements
    return doc_rewritten
